import { useEffect, useState } from 'react'
import { Keywords as API, Products } from '../api'

export default function Keywords(){
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const refresh = ()=> API.list().then(setItems)
  useEffect(() => { refresh() }, [])
  const fetchNow = async ()=>{
    setLoading(true)
    await API.fetch()
    await refresh()
    setLoading(false)
  }
  const recommend = async (id:number)=>{
    try {
      await Products.recommend(id)
      alert('추천 생성 완료')
    } catch (err:any) {
      const reason = err?.response?.data?.detail?.reason || err?.response?.data?.detail?.message || err?.message
      alert('추천 실패: ' + (reason || '알 수 없는 오류'))
    }
  }
  return (
    <div className="card">
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <h3>키워드</h3>
        <button className="btn" onClick={fetchNow} disabled={loading}>{loading? '불러오는 중...' : 'DataLab에서 수집'}</button>
      </div>
      <table>
        <thead><tr><th>ID</th><th>키워드</th><th>점수</th><th>카테고리</th><th></th></tr></thead>
        <tbody>
          {items.map(k => (
            <tr key={k.id}>
              <td className="mono">{k.id}</td>
              <td>{k.text}</td>
              <td>{k.score?.toFixed?.(2)}</td>
              <td>{k.category}</td>
              <td><button className="btn secondary" onClick={()=>recommend(k.id)}>상품 추천</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
