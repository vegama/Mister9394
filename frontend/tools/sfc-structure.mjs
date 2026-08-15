import {readFileSync,readdirSync,statSync} from 'node:fs'
import {extname,join,relative,resolve} from 'node:path'
import {fileURLToPath} from 'node:url'

const ATTRIBUTE_NAME=/[^\s=/>]+/y

export function startTags(source){
  const tags=[]
  let i=0
  while(i<source.length){
    const start=source.indexOf('<',i)
    if(start<0)break
    if(source.startsWith('<!--',start)){
      const end=source.indexOf('-->',start+4); i=end<0?source.length:end+3; continue
    }
    if(source[start+1]==='/'||source[start+1]==='!'||source[start+1]==='?'){i=start+1;continue}
    let p=start+1
    while(p<source.length&&/\s/.test(source[p]))p++
    const tagMatch=/[A-Za-z][\w:.-]*/y;tagMatch.lastIndex=p
    const tag=tagMatch.exec(source)?.[0]
    if(!tag){i=start+1;continue}
    p=tagMatch.lastIndex
    const attributes=[]
    while(p<source.length){
      while(p<source.length&&/\s/.test(source[p]))p++
      if(source[p]==='>'||(source[p]==='/'&&source[p+1]==='>'))break
      ATTRIBUTE_NAME.lastIndex=p
      const attrMatch=ATTRIBUTE_NAME.exec(source)
      if(!attrMatch){p++;continue}
      const name=attrMatch[0]
      const attrIndex=p
      p=ATTRIBUTE_NAME.lastIndex
      while(p<source.length&&/\s/.test(source[p]))p++
      let value=null
      if(source[p]==='='){
        p++
        while(p<source.length&&/\s/.test(source[p]))p++
        const quote=source[p]
        if(quote==='"'||quote==="'"){
          const valueStart=++p
          while(p<source.length){
            if(source[p]===quote){value=source.slice(valueStart,p);p++;break}
            if(source[p]==='\\')p+=2;else p++
          }
        }else{
          const valueStart=p
          while(p<source.length&&!/[\s>]/.test(source[p]))p++
          value=source.slice(valueStart,p)
        }
      }
      attributes.push({name,value,index:attrIndex})
    }
    tags.push({tag,index:start,attributes})
    if(['script','style'].includes(tag.toLowerCase())){
      const close=source.indexOf(`</${tag}>`,p+1)
      i=close<0?source.length:close+tag.length+3
    }else i=p<source.length?p+1:source.length
  }
  return tags
}

export function duplicateAttributes(source){
  const duplicates=[]
  for(const row of startTags(source)){
    const seen=new Map()
    for(const attr of row.attributes){
      const canonical=attr.name.toLowerCase()
      if(seen.has(canonical))duplicates.push({tag:row.tag,name:attr.name,index:row.index,firstIndex:seen.get(canonical)})
      else seen.set(canonical,attr.index)
    }
  }
  return duplicates
}

export function scanVueTree(root){
  const out=[]
  function walk(dir){
    for(const name of readdirSync(dir)){
      const path=join(dir,name)
      if(statSync(path).isDirectory())walk(path)
      else if(extname(path)==='.vue'){
        for(const issue of duplicateAttributes(readFileSync(path,'utf8')))out.push({...issue,file:relative(root,path)})
      }
    }
  }
  walk(root)
  return out
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const root=resolve(process.argv[2]||fileURLToPath(new URL('../src',import.meta.url)))
  const issues=scanVueTree(root)
  if(issues.length){
    for(const issue of issues)console.error(`${issue.file}: <${issue.tag}> atributo duplicado \"${issue.name}\"`)
    process.exitCode=1
  }else console.log('SFC structure OK: no duplicate attributes')
}
