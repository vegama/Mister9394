from __future__ import annotations

"""Small, read-only Microsoft Jet 4 MDB reader used by Míster 93/94.

This is intentionally narrow: it implements the page, TDEF, row and scalar
pieces needed to import the supplied football database without requiring an
ODBC/Access runtime.  It never writes the source MDB.

The layout follows the public MDB Tools Jet4 format documentation and its
reader implementation.  Unsupported long-value cases are preserved as bytes
rather than guessed.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import struct
from typing import Any, Iterator

PAGE_SIZE = 4096
OFFSET_MASK = 0x1FFF
ROW_COUNT_OFFSET = 0x0C

MDB_BOOL = 0x01
MDB_BYTE = 0x02
MDB_INT = 0x03
MDB_LONGINT = 0x04
MDB_MONEY = 0x05
MDB_FLOAT = 0x06
MDB_DOUBLE = 0x07
MDB_DATETIME = 0x08
MDB_BINARY = 0x09
MDB_TEXT = 0x0A
MDB_OLE = 0x0B
MDB_MEMO = 0x0C
MDB_REPID = 0x0F
MDB_NUMERIC = 0x10
MDB_COMPLEX = 0x12

TYPE_NAMES = {
    MDB_BOOL: "bool", MDB_BYTE: "byte", MDB_INT: "int16", MDB_LONGINT: "int32",
    MDB_MONEY: "money", MDB_FLOAT: "float", MDB_DOUBLE: "double",
    MDB_DATETIME: "datetime", MDB_BINARY: "binary", MDB_TEXT: "text",
    MDB_OLE: "ole", MDB_MEMO: "memo", MDB_REPID: "repid",
    MDB_NUMERIC: "numeric", MDB_COMPLEX: "complex",
}

OBJECT_TYPES = {
    0: "form", 1: "table", 2: "macro", 3: "system_table", 4: "report",
    5: "query", 6: "linked_table", 7: "module", 8: "relationship",
    9: "unknown_09", 10: "user_access", 11: "database_property",
}


class MDBError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class Jet4Column:
    name: str
    col_type: int
    col_num: int
    var_col_num: int
    row_col_num: int
    is_fixed: bool
    fixed_offset: int
    size: int
    scale: int = 0
    precision: int = 0

    @property
    def type_name(self) -> str:
        return TYPE_NAMES.get(self.col_type, f"unknown_{self.col_type:02x}")


@dataclass(frozen=True, slots=True)
class Jet4Table:
    name: str
    page: int
    num_rows: int
    max_cols: int
    num_var_cols: int
    num_cols: int
    num_indexes: int
    num_real_indexes: int
    table_type: int
    columns: tuple[Jet4Column, ...]


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    name: str
    object_type: int
    table_page: int
    flags: int
    raw_id: int

    @property
    def object_type_name(self) -> str:
        return OBJECT_TYPES.get(self.object_type, f"unknown_{self.object_type}")


@dataclass(frozen=True, slots=True)
class RawRow:
    page: int
    row: int
    deleted: bool
    lookup: bool
    values: dict[str, Any]


def _u16(buf: bytes, off: int) -> int:
    return struct.unpack_from("<H", buf, off)[0]


def _i16(buf: bytes, off: int) -> int:
    return struct.unpack_from("<h", buf, off)[0]


def _u32(buf: bytes, off: int) -> int:
    return struct.unpack_from("<I", buf, off)[0]


def _i32(buf: bytes, off: int) -> int:
    return struct.unpack_from("<i", buf, off)[0]


def _decompress_unicode(payload: bytes) -> bytes:
    """Expand Access 'Unicode Compression' payload to UTF-16LE bytes."""
    out = bytearray()
    compressed = True
    i = 0
    while i < len(payload):
        byte = payload[i]
        if byte == 0:
            compressed = not compressed
            i += 1
        elif compressed:
            out.extend((byte, 0))
            i += 1
        else:
            if i + 1 >= len(payload):
                break
            out.extend(payload[i:i + 2])
            i += 2
    return bytes(out)


def decode_jet4_text(data: bytes) -> str:
    if not data:
        return ""
    if data.startswith(b"\xff\xfe"):
        data = _decompress_unicode(data[2:])
    if len(data) % 2:
        data = data[:-1]
    return data.decode("utf-16le", errors="replace").rstrip("\x00")


class _TDefCursor:
    """Cursor over a Jet4 table-definition chain.

    The first TDEF page exposes bytes 0..4095.  Continuation pages keep an
    8-byte page header, so logical offsets beyond the first page advance by
    4096-8 bytes per chained page.  This mirrors MDB Tools' read_pg_if_n
    behaviour and lets column descriptors/names span physical pages.
    """

    def __init__(self, db: "Jet4MDB", first_page: int, pos: int = 0):
        self.db = db
        self.page_number = first_page
        self.pg = db.page(first_page)
        self.pos = pos
        self._seen = {first_page}
        while self.pos >= PAGE_SIZE:
            self._follow_next()
            self.pos -= PAGE_SIZE - 8

    def _follow_next(self) -> None:
        next_page = _u32(self.pg, 4)
        if next_page == 0:
            raise MDBError(f"TDEF {self.page_number} termina antes de tiempo")
        if next_page in self._seen:
            raise MDBError(f"ciclo en cadena TDEF: página {next_page}")
        self._seen.add(next_page)
        self.page_number = next_page
        self.pg = self.db.page(next_page)
        if self.pg[0] != 0x02:
            raise MDBError(
                f"continuación TDEF inválida en página {next_page} (tipo={self.pg[0]})"
            )
        self.pos = 8

    def read(self, size: int) -> bytes:
        if size < 0:
            raise MDBError("lectura TDEF con tamaño negativo")
        out = bytearray()
        remaining = size
        while remaining:
            if self.pos >= PAGE_SIZE:
                self._follow_next()
            take = min(remaining, PAGE_SIZE - self.pos)
            if take <= 0:
                self._follow_next()
                continue
            out.extend(self.pg[self.pos:self.pos + take])
            self.pos += take
            remaining -= take
            if remaining and self.pos >= PAGE_SIZE:
                self._follow_next()
        return bytes(out)

    def read_u16(self) -> int:
        data = self.read(2)
        if len(data) != 2:
            raise MDBError("TDEF truncada leyendo uint16")
        return _u16(data, 0)


class Jet4MDB:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._blob = self.path.read_bytes()
        if len(self._blob) < PAGE_SIZE * 3:
            raise MDBError("MDB demasiado pequeño")
        if self._blob[0x14] != 0x01:
            raise MDBError(f"se esperaba Jet4 (versión 0x01), encontrada 0x{self._blob[0x14]:02x}")
        if b"Standard Jet DB" not in self._blob[:64]:
            raise MDBError("cabecera Jet no reconocida")
        self.page_count = len(self._blob) // PAGE_SIZE
        self._catalog_cache: tuple[CatalogEntry, ...] | None = None
        self._table_cache: dict[int, Jet4Table] = {}

    def page(self, number: int) -> bytes:
        if number < 0 or number >= self.page_count:
            raise MDBError(f"página fuera de rango: {number}")
        start = number * PAGE_SIZE
        return self._blob[start:start + PAGE_SIZE]

    def read_table_def(self, page_number: int, name: str = "") -> Jet4Table:
        if page_number in self._table_cache:
            cached = self._table_cache[page_number]
            if name and not cached.name:
                cached = Jet4Table(name=name, page=cached.page, num_rows=cached.num_rows,
                                   max_cols=cached.max_cols, num_var_cols=cached.num_var_cols,
                                   num_cols=cached.num_cols, num_indexes=cached.num_indexes,
                                   num_real_indexes=cached.num_real_indexes,
                                   table_type=cached.table_type, columns=cached.columns)
                self._table_cache[page_number] = cached
            return cached
        pg = self.page(page_number)
        if pg[0] != 0x02:
            raise MDBError(f"página {page_number} no es TDEF (tipo={pg[0]})")

        num_rows = _u32(pg, 16)
        table_type = pg[40]
        max_cols = _u16(pg, 41)
        num_var_cols = _u16(pg, 43)
        num_cols = _u16(pg, 45)
        num_indexes = _u32(pg, 47)
        num_real_indexes = _u32(pg, 51)
        if num_cols > 1024 or num_real_indexes > 1024:
            raise MDBError(f"TDEF inválida en página {page_number}")

        cursor = _TDefCursor(self, page_number, 63 + num_real_indexes * 12)
        raw_columns: list[dict[str, Any]] = []
        for _ in range(num_cols):
            entry = cursor.read(25)
            if len(entry) != 25:
                raise MDBError(f"TDEF truncada en página {page_number}")
            raw_columns.append({
                "col_type": entry[0],
                # MDB Tools reads the low byte here; Jet4 col_num is bounded by 255.
                "col_num": entry[5],
                "var_col_num": _u16(entry, 7),
                "row_col_num": _u16(entry, 9),
                "scale": entry[11],
                "precision": entry[12],
                "is_fixed": bool(entry[15] & 0x01),
                "fixed_offset": _u16(entry, 21),
                "size": 0 if entry[0] == MDB_BOOL else _u16(entry, 23),
            })

        for col in raw_columns:
            name_len = cursor.read_u16()
            if name_len > 4096:
                raise MDBError(
                    f"nombre de columna inválido ({name_len} bytes) en TDEF {page_number}"
                )
            raw_name = cursor.read(name_len)
            col["name"] = decode_jet4_text(raw_name)

        columns = tuple(
            Jet4Column(**col) for col in sorted(raw_columns, key=lambda c: c["col_num"])
        )
        table = Jet4Table(
            name=name, page=page_number, num_rows=num_rows, max_cols=max_cols,
            num_var_cols=num_var_cols, num_cols=num_cols, num_indexes=num_indexes,
            num_real_indexes=num_real_indexes, table_type=table_type, columns=columns,
        )
        self._table_cache[page_number] = table
        return table

    def data_pages(self, table_page: int) -> Iterator[tuple[int, bytes]]:
        for number in range(self.page_count):
            pg = self.page(number)
            if pg[0] == 0x01 and _u32(pg, 4) == table_page:
                yield number, pg

    @staticmethod
    def _row_bounds(pg: bytes, row: int) -> tuple[int, int, int]:
        rows = _u16(pg, ROW_COUNT_OFFSET)
        if row < 0 or row >= rows:
            raise MDBError(f"fila {row} fuera de rango ({rows})")
        raw_start = _u16(pg, ROW_COUNT_OFFSET + 2 + row * 2)
        start = raw_start & OFFSET_MASK
        next_start = PAGE_SIZE if row == 0 else (_u16(pg, ROW_COUNT_OFFSET + row * 2) & OFFSET_MASK)
        if start >= PAGE_SIZE or start > next_start or next_start > PAGE_SIZE:
            raise MDBError("offset de fila inválido")
        return raw_start, start, next_start

    @staticmethod
    def _decode_scalar(col: Jet4Column, data: bytes, bool_bit: bool | None = None) -> Any:
        if col.col_type == MDB_BOOL:
            return bool(bool_bit)
        if not data:
            return None
        try:
            if col.col_type == MDB_BYTE:
                return data[0]
            if col.col_type == MDB_INT and len(data) >= 2:
                return struct.unpack_from("<h", data)[0]
            if col.col_type == MDB_LONGINT and len(data) >= 4:
                return struct.unpack_from("<i", data)[0]
            if col.col_type == MDB_MONEY and len(data) >= 8:
                return struct.unpack_from("<q", data)[0] / 10000
            if col.col_type == MDB_FLOAT and len(data) >= 4:
                return struct.unpack_from("<f", data)[0]
            if col.col_type == MDB_DOUBLE and len(data) >= 8:
                return struct.unpack_from("<d", data)[0]
            if col.col_type == MDB_DATETIME and len(data) >= 8:
                days = struct.unpack_from("<d", data)[0]
                if not (-100000 < days < 300000):
                    return days
                return datetime(1899, 12, 30) + timedelta(days=days)
            if col.col_type == MDB_TEXT:
                return decode_jet4_text(data)
            if col.col_type == MDB_REPID and len(data) >= 16:
                return data[:16].hex()
            if col.col_type in (MDB_BINARY, MDB_OLE, MDB_MEMO, MDB_NUMERIC, MDB_COMPLEX):
                return data
        except (struct.error, OverflowError, ValueError):
            return data
        return data

    def crack_row(self, table: Jet4Table, row_bytes: bytes) -> dict[str, Any]:
        if len(row_bytes) < 3:
            raise MDBError("fila demasiado corta")
        row_cols = _u16(row_bytes, 0)
        if row_cols > table.max_cols or row_cols > 2048:
            raise MDBError(f"número de columnas de fila inválido: {row_cols}")
        bitmask_size = (row_cols + 7) // 8
        if bitmask_size + 2 >= len(row_bytes):
            raise MDBError("máscara null inválida")
        nullmask = row_bytes[len(row_bytes) - bitmask_size:]

        row_var_cols = 0
        var_offsets: list[int] = []
        if table.num_var_cols > 0:
            var_count_pos = len(row_bytes) - bitmask_size - 2
            row_var_cols = _u16(row_bytes, var_count_pos)
            if row_var_cols > table.num_var_cols or row_var_cols > row_cols:
                raise MDBError(f"número de variables inválido: {row_var_cols}")
            # mdb_crack_row4 reads offsets backwards from row_end-bitmask-3,
            # including a final EOD offset at index row_var_cols.
            row_end = len(row_bytes) - 1
            for i in range(row_var_cols + 1):
                pos = row_end - bitmask_size - 3 - i * 2
                if pos < 0 or pos + 2 > len(row_bytes):
                    raise MDBError("tabla de offsets variables inválida")
                var_offsets.append(_u16(row_bytes, pos))
            if any(v < 0 or v > len(row_bytes) for v in var_offsets):
                raise MDBError("offset variable fuera de fila")

        row_fixed_cols = row_cols - row_var_cols
        fixed_found = 0
        values: dict[str, Any] = {}
        for col in table.columns:
            if col.col_num >= row_cols:
                values[col.name] = None
                continue
            byte_num = col.col_num // 8
            bit_num = col.col_num % 8
            bit_set = byte_num < len(nullmask) and bool(nullmask[byte_num] & (1 << bit_num))
            is_null = not bit_set

            if col.col_type == MDB_BOOL:
                # Jet stores BOOL in the null bitmap itself.
                values[col.name] = bit_set
                continue

            start: int | None = None
            end: int | None = None
            if col.is_fixed and fixed_found < row_fixed_cols:
                start = 2 + col.fixed_offset
                end = start + col.size
                fixed_found += 1
            elif (not col.is_fixed) and col.var_col_num < row_var_cols:
                start = var_offsets[col.var_col_num]
                end = var_offsets[col.var_col_num + 1]
            else:
                is_null = True

            if is_null or start is None or end is None:
                values[col.name] = None
                continue
            if start < 0 or end < start or end > len(row_bytes):
                raise MDBError(f"campo {col.name} apunta fuera de fila ({start}:{end}/{len(row_bytes)})")
            values[col.name] = self._decode_scalar(col, row_bytes[start:end])
        return values

    def iter_rows(self, table: Jet4Table, *, include_deleted: bool = False) -> Iterator[RawRow]:
        for page_num, pg in self.data_pages(table.page):
            row_count = _u16(pg, ROW_COUNT_OFFSET)
            for row_num in range(row_count):
                try:
                    raw_start, start, end = self._row_bounds(pg, row_num)
                except MDBError:
                    continue
                lookup = bool(raw_start & 0x8000)
                deleted = bool(raw_start & 0x4000)
                if deleted and not include_deleted:
                    continue
                # Overflow/lookup rows require following a data pointer. They are
                # uncommon in the catalogue and are skipped rather than guessed.
                if lookup:
                    continue
                try:
                    values = self.crack_row(table, pg[start:end])
                except MDBError:
                    continue
                yield RawRow(page=page_num, row=row_num, deleted=deleted, lookup=lookup, values=values)

    def catalog(self) -> tuple[CatalogEntry, ...]:
        if self._catalog_cache is not None:
            return self._catalog_cache
        table = self.read_table_def(2, "MSysObjects")
        entries: list[CatalogEntry] = []
        for row in self.iter_rows(table):
            v = row.values
            name = v.get("Name")
            raw_id = v.get("Id")
            raw_type = v.get("Type")
            flags = v.get("Flags")
            if not isinstance(name, str) or not isinstance(raw_id, int) or not isinstance(raw_type, int):
                continue
            entries.append(CatalogEntry(
                name=name,
                object_type=raw_type & 0x7F,
                table_page=raw_id & 0x00FFFFFF,
                flags=int(flags or 0),
                raw_id=raw_id,
            ))
        self._catalog_cache = tuple(entries)
        return self._catalog_cache

    def catalog_entry(self, name: str) -> CatalogEntry | None:
        needle = name.casefold()
        for entry in self.catalog():
            if entry.name.casefold() == needle:
                return entry
        return None

    def table(self, name: str) -> Jet4Table:
        entry = self.catalog_entry(name)
        if entry is None:
            raise MDBError(f"tabla no encontrada: {name}")
        if entry.object_type not in (1, 3, 6):
            raise MDBError(f"{name} no es una tabla (tipo={entry.object_type_name})")
        return self.read_table_def(entry.table_page, name)

    def rows(self, name: str, *, limit: int | None = None) -> list[dict[str, Any]]:
        table = self.table(name)
        out: list[dict[str, Any]] = []
        for row in self.iter_rows(table):
            out.append(row.values)
            if limit is not None and len(out) >= limit:
                break
        return out


def json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, bytes):
        return {"bytes": len(value), "hex_prefix": value[:24].hex()}
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value
