import { NavLink, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Keywords from './pages/Keywords'
import Products from './pages/Products'
import Drafts from './pages/Drafts'
import Settings from './pages/Settings'
import Playbook from './pages/Playbook'

export default function App(){
  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>CP Orchestrator</h1>
        <nav className="nav">
          <NavLink to="/" end>대시보드</NavLink>
          <NavLink to="/keywords">키워드</NavLink>
          <NavLink to="/products">상품 후보/HITL</NavLink>
          <NavLink to="/drafts">초안/게시</NavLink>
          <NavLink to="/playbook">전략/운영</NavLink>
          <NavLink to="/settings">설정</NavLink>
        </nav>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<Dashboard/>} />
          <Route path="/keywords" element={<Keywords/>} />
          <Route path="/products" element={<Products/>} />
          <Route path="/drafts" element={<Drafts/>} />
          <Route path="/playbook" element={<Playbook/>} />
          <Route path="/settings" element={<Settings/>} />
        </Routes>
      </main>
    </div>
  )
}
