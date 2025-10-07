import React, { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
// @ts-ignore
import rehypeRaw from 'rehype-raw'

export default function Playbook(){
  const [md, setMd] = useState<string>('')
  useEffect(()=>{
    fetch('/playbook.md').then(r=> r.text()).then(setMd).catch(()=> setMd('# 플레이북 로드 실패'))
  },[])
  return (
    <div className="card">
      <h3>극한의 수익률 플레이북</h3>
      <div style={{background:'#0f1320', padding:12, borderRadius:8}}>
        <ReactMarkdown rehypePlugins={[rehypeRaw]}>{md}</ReactMarkdown>
      </div>
    </div>
  )
}
