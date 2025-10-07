import { useEffect, useState } from 'react'
import { Affiliate } from '../api'

export default function Products(){
  const [items, setItems] = useState<any[]>([])
  const [urlMap, setUrlMap] = useState<Record<number, string>>({})
  const [htmlMap, setHtmlMap] = useState<Record<number, string>>({})
  const refresh = ()=> Affiliate.pending().then(setItems)
  useEffect(()=>{ refresh() }, [])

  const map = async (id:number)=>{
    const url = urlMap[id]
    if(!url) return alert('제휴 링크를 입력하세요')
    const html = htmlMap[id]
    await Affiliate.map(id, url, html)
    await refresh()
  }

  return (
    <div className="card">
      <h3>상품 후보 / 제휴 링크 매핑 (HITL)</h3>
      <table>
        <thead><tr><th>ID</th><th>키워드ID</th><th>제목 추정</th><th>브랜드/모델</th><th>쿠팡</th><th>제휴 링크</th><th>제휴 HTML</th><th></th></tr></thead>
        <tbody>
          {items.map(it => (
            <tr key={it.id}>
              <td className="mono">{it.id}</td>
              <td className="mono">{it.keyword_id}</td>
              <td>{it.title_guess}</td>
              <td>{it.brand} {it.model}</td>
              <td>{it.coupang_url ? <a href={it.coupang_url} target="_blank" rel="noreferrer">열기</a> : '-'}</td>
              <td style={{width: '26%'}}>
                <input className="input" placeholder="쿠팡 파트너스 제휴 링크 붙여넣기" value={urlMap[it.id]||''} onChange={e=>setUrlMap(s=>({...s, [it.id]: e.target.value}))} />
              </td>
              <td style={{width: '30%'}}>
                <textarea className="input" placeholder="쿠팡 파트너스 HTML (선택)" rows={3} value={htmlMap[it.id]||''} onChange={e=>setHtmlMap(s=>({...s, [it.id]: e.target.value}))} />
              </td>
              <td>
                <button className="btn" onClick={()=>map(it.id)}>매핑</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
