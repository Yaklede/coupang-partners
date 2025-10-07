import { useEffect, useState } from 'react'
import { Metrics } from '../api'

export default function Dashboard(){
  const [posts, setPosts] = useState<any>({})
  const [budget, setBudget] = useState<any>({ daily: [] })
  useEffect(() => {
    Metrics.posts().then(setPosts)
    Metrics.budget().then(setBudget)
  }, [])
  return (
    <div className="row">
      <div className="card" style={{gridColumn:'span 6'}}>
        <h3>포스트 현황</h3>
        <div>전체: <b>{posts.total ?? '-'}</b></div>
        <div>게시됨: <b>{posts.published ?? '-'}</b></div>
      </div>
      <div className="card" style={{gridColumn:'span 6'}}>
        <h3>예산 사용</h3>
        <table>
          <thead><tr><th>날짜</th><th>토큰</th><th>USD</th><th>CAP</th></tr></thead>
          <tbody>
            {budget.daily.map((d:any)=> (
              <tr key={d.date}><td>{d.date}</td><td>{d.token_used}</td><td>${d.usd_spent?.toFixed?.(3)}</td><td>${d.cap}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

