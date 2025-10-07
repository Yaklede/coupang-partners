import { useEffect, useState } from 'react'
import { Products, Posts } from '../api'
import ReactMarkdown from 'react-markdown'
// @ts-ignore - types are included with package
import rehypeRaw from 'rehype-raw'
import { marked } from 'marked'

export default function Drafts(){
  const [mapped, setMapped] = useState<any[]>([])
  const [posts, setPosts] = useState<any[]>([])
  const [md, setMd] = useState<string>('')
  const [schedule, setSchedule] = useState<string>('')
  const [templateType, setTemplateType] = useState<string>('A')
  const [ti, setTi] = useState<any>({ period:'2주', place:'집', activity:'일상', measures:'체감 위주', comparisons:'동급 1~2개', reader_points:'소음/보관/가성비', photo_keywords:'사용 장면, 보관, 구성품' })
  const [selected, setSelected] = useState<Record<number, boolean>>({})
  const refresh = ()=> Posts.list().then(setPosts)
  useEffect(()=>{ refresh(); Products.list('mapped').then(setMapped) }, [])

  const makeDraft = async (productId:number)=>{
    try {
      const r = await Posts.draft(productId, templateType, ti)
      await refresh()
      alert(`초안 생성: #${r.id}`)
    } catch (err:any) {
      const reason = err?.response?.data?.detail?.reason || err?.response?.data?.detail?.message || err?.message
      alert('초안 생성 실패: ' + (reason || '알 수 없는 오류'))
    }
  }
  const publish = async (postId:number)=>{
    await Posts.publish(postId, schedule || undefined)
    await refresh()
  }
  const makeCompare = async ()=>{
    const ids = Object.entries(selected).filter(([,v])=>v).map(([k])=>Number(k))
    if(ids.length < 2){ alert('최소 2개 이상 선택하세요'); return }
    try{
      const r = await Posts.draftCompare(ids, { scenario: '가성비/조용함/내구' })
      await refresh()
      alert(`비교 초안 생성: #${r.id}`)
    }catch(err:any){
      const reason = err?.response?.data?.detail?.reason || err?.response?.data?.detail?.message || err?.message
      alert('비교 초안 실패: ' + (reason || '알 수 없는 오류'))
    }
  }
  return (
    <div className="row">
      <div className="card" style={{gridColumn:'span 12'}}>
        <h3>작성 템플릿 선택</h3>
        <div style={{display:'flex', gap:12, flexWrap:'wrap'}}>
          <label>템플릿
            <select className="input" value={templateType} onChange={e=>setTemplateType(e.target.value)}>
              <option value="A">A. 실사용 리뷰형</option>
              <option value="B">B. 비교 가이드형</option>
              <option value="C">C. 리스트·큐레이션형</option>
              <option value="D">D. 문제 해결형</option>
              <option value="E">E. 시즌/행사 특가형</option>
            </select>
          </label>
          {templateType==='A' && (
            <>
              <input className="input" style={{minWidth:180}} placeholder="사용 기간" value={ti.period} onChange={e=>setTi({...ti, period:e.target.value})} />
              <input className="input" style={{minWidth:160}} placeholder="장소" value={ti.place} onChange={e=>setTi({...ti, place:e.target.value})} />
              <input className="input" style={{minWidth:180}} placeholder="활동" value={ti.activity} onChange={e=>setTi({...ti, activity:e.target.value})} />
              <input className="input" style={{minWidth:220}} placeholder="측정 항목/수치" value={ti.measures} onChange={e=>setTi({...ti, measures:e.target.value})} />
              <input className="input" style={{minWidth:220}} placeholder="비교 대상" value={ti.comparisons} onChange={e=>setTi({...ti, comparisons:e.target.value})} />
              <input className="input" style={{minWidth:240}} placeholder="독자 궁금 포인트" value={ti.reader_points} onChange={e=>setTi({...ti, reader_points:e.target.value})} />
              <input className="input" style={{minWidth:260}} placeholder="사진 키워드" value={ti.photo_keywords} onChange={e=>setTi({...ti, photo_keywords:e.target.value})} />
            </>
          )}
        </div>
      </div>
      <div className="card" style={{gridColumn:'span 6'}}>
        <h3>초안 생성 (매핑 완료된 후보)</h3>
        <div style={{marginBottom:8}}>
          <button className="btn secondary" onClick={makeCompare}>선택 항목 비교 초안 생성(B)</button>
        </div>
        <table>
          <thead><tr><th></th><th>ID</th><th>제목 추정</th><th></th></tr></thead>
          <tbody>
            {mapped.map(p=> (
              <tr key={p.id}>
                <td><input type="checkbox" checked={!!selected[p.id]} onChange={e=>setSelected(s=>({...s, [p.id]: e.target.checked}))} /></td>
                <td>{p.id}</td>
                <td>{p.title_guess}</td>
                <td><button className="btn" onClick={()=>makeDraft(p.id)}>초안 생성</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="card" style={{gridColumn:'span 6'}}>
        <h3>게시/예약</h3>
        <div style={{margin:'8px 0'}}>
          <input className="input" placeholder="ISO 스케줄(선택) 예: 2025-10-07T09:15:00" value={schedule} onChange={e=>setSchedule(e.target.value)} />
        </div>
        <table>
          <thead><tr><th>ID</th><th>제목</th><th>상태</th><th></th></tr></thead>
          <tbody>
            {posts.map(p=> (
              <tr key={p.id}>
                <td>{p.id}</td>
                <td>{p.title}</td>
                <td>{p.status}</td>
                <td>
                  <button className="btn" onClick={()=>publish(p.id)}>{schedule? '예약' : '즉시 게시'}</button>{' '}
                  <button className="btn secondary" onClick={()=>setMd(p.body_md||'')}>미리보기</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="card" style={{gridColumn:'span 12'}}>
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
          <h3>미리보기</h3>
          <div style={{display:'flex', gap:8}}>
            <button className="btn secondary" onClick={async()=>{ await navigator.clipboard.writeText(md||''); alert('마크다운을 복사했습니다') }}>마크다운 복사</button>
            <button className="btn secondary" onClick={async()=>{
              const html = (marked.parse(md||'') as string) || ''
              await navigator.clipboard.writeText(html)
              alert('HTML을 복사했습니다')
            }}>HTML 복사</button>
            <button className="btn" onClick={async()=>{
              const html = buildNaverFriendlyHTML(md||'')
              try{
                // Prefer rich HTML clipboard so editors keep formatting
                const item = new ClipboardItem({
                  'text/html': new Blob([html], {type:'text/html'}),
                  'text/plain': new Blob([md||''], {type:'text/plain'})
                })
                // @ts-ignore
                await navigator.clipboard.write([item])
                alert('네이버용 서식(HTML)으로 복사했습니다')
              }catch(e){
                await navigator.clipboard.writeText(html)
                alert('네이버용 HTML을 텍스트로 복사했습니다')
              }
            }}>서식 복사(네이버용)</button>
          </div>
        </div>
        <div style={{background:'#0f1320', padding:12, borderRadius:8}}>
          <ReactMarkdown rehypePlugins={[rehypeRaw]}>{md}</ReactMarkdown>
        </div>
      </div>
    </div>
  )
}

function buildNaverFriendlyHTML(md: string): string {
  // 1) Convert MD to HTML
  let html = (marked.parse(md || '') as string) || ''
  // 2) Post-process tables with inline borders/cell padding for paste retention
  html = html.replace(/<table>/g, '<table style="border-collapse:collapse; width:100%;" border="1">')
             .replace(/<th>/g, '<th style="border:1px solid #d0d7de; padding:8px; background:#f6f8fa;">')
             .replace(/<td>/g, '<td style="border:1px solid #d0d7de; padding:8px;">')
             .replace(/<tr>/g, '<tr style="border:1px solid #d0d7de;">')
  // 3) Headings margins (inline)
  html = html.replace(/<h2>/g, '<h2 style="margin:20px 0 12px;">')
             .replace(/<h3>/g, '<h3 style="margin:16px 0 10px;">')
             .replace(/<p>/g, '<p style="margin:10px 0;">')
  // 4) Blockquote styling
  html = html.replace(/<blockquote>/g, '<blockquote style="margin:12px 0; padding:8px 12px; border-left:4px solid #d0d7de; background:#f9fbfd;">')
  // 5) Code blocks
  html = html.replace(/<pre>/g, '<pre style="background:#0f1320; color:#eaeef2; padding:12px; border-radius:6px; overflow:auto;">')
             .replace(/<code>/g, '<code style="background:#0f1320; color:#eaeef2; padding:2px 4px; border-radius:4px;">')
  // 6) Wrap in a container div to avoid style bleed
  return `<div>${html}</div>`
}
