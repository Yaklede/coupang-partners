import axios from 'axios'

// Resolve API base URL with sensible defaults across dev/docker/prod
// Priority: VITE_API_BASE_URL > origin has port? use '/api' (proxy) : 'http://localhost:8000/api'
const resolvedBase = ((): string => {
  const env = (import.meta as any).env
  const fromEnv = env && env.VITE_API_BASE_URL
  if (fromEnv) return fromEnv.replace(/\/$/, '')
  if (window.location.port) return '/api'
  return 'http://localhost:8000/api'
})()

export const api = axios.create({ baseURL: resolvedBase })

export const Keywords = {
  fetch: () => api.post('/keywords/fetch').then(r => r.data as any[]),
  list: () => api.get('/keywords').then(r => r.data as any[]),
}

export const Products = {
  recommend: (keywordId: number) => api.post(`/products/recommend/${keywordId}`).then(r => r.data as any[]),
  list: (status?: string) => api.get('/products', { params: { status } }).then(r => r.data as any[]),
}

export const Affiliate = {
  map: (productId: number, url: string, html?: string) => api.post('/affiliate/map', { product_id: productId, url, html }).then(r => r.data),
  pending: () => api.get('/affiliate/pending').then(r => r.data as any[]),
}

export const Posts = {
  draft: (productId: number, templateType?: string, templateInput?: any) =>
    api.post('/posts/draft', { product_id: productId, template_type: templateType, template_input: templateInput }).then(r => r.data),
  draftCompare: (productIds: number[], templateInput?: any) =>
    api.post('/posts/draft/compare', { product_ids: productIds, template_input: templateInput }).then(r => r.data),
  publish: (postId: number, schedule?: string) => api.post('/posts/publish', { post_id: postId, schedule }).then(r => r.data),
  list: () => api.get('/posts').then(r => r.data as any[]),
}

export const Metrics = {
  posts: () => api.get('/metrics/posts').then(r => r.data),
  budget: () => api.get('/metrics/budget').then(r => r.data),
}

export const Auth = {
  naverLoginUrl: () => api.get('/auth/naver/login').then(r => r.data.login_url as string),
  naverStatus: () => api.get('/auth/naver/status').then(r => r.data),
}

export const Admin = {
  resetDb: () => api.post('/admin/reset-db').then(r => r.data),
  deleteKeywords: (date?: string) => api.delete('/admin/keywords', { params: date ? { date } : {} }).then(r => r.data),
  dedupKeywords: (date: string) => api.post('/admin/dedup-keywords', null, { params: { date } }).then(r => r.data),
  getAIConfig: () => api.get('/admin/ai-config').then(r => r.data),
  setAIConfig: (data: any) => api.post('/admin/ai-config', data).then(r => r.data),
}

export const Diagnostics = {
  ai: () => api.get('/diagnostics/ai').then(r => r.data),
}
