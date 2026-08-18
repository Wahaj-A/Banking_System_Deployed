// Cleanly ensure base URL without double slashes or trailing /api
const BASE_URL = (import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://127.0.0.1:8000' : window.location.origin)).replace(/\/+$/, '')
const API_URL = BASE_URL.endsWith('/api') ? BASE_URL : `${BASE_URL}/api`

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  let data = null
  try {
    data = await res.json()
  } catch {
    // no JSON body
  }

  if (!res.ok) {
    const message = data?.detail || `Request failed (${res.status})`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }

  return data
}

export const api = {
  // Auth Routes
  signup: (email, password) => request('/signup', { method: 'POST', body: JSON.stringify({ email, password }) }),
  login: (email, password) => request('/login', { method: 'POST', body: JSON.stringify({ email, password }) }),

  // Banking Routes
  listAccounts: () => request('/accounts'),
  getAccount: (id, email) => request(`/accounts/${id}?email=${encodeURIComponent(email)}`),
  createAccount: (name, starting_balance, email) => request('/accounts', { method: 'POST', body: JSON.stringify({ name, starting_balance, email }) }),
  transactionHistory: (id, email) => request(`/accounts/${id}/transactions?email=${encodeURIComponent(email)}`),

  // Transaction Routes
  deposit: (account_id, amount, email) => request('/deposit', { method: 'POST', body: JSON.stringify({ account_id, amount, email }) }),
  withdraw: (account_id, amount, email) => request('/withdraw', { method: 'POST', body: JSON.stringify({ account_id, amount, email }) }),
  transfer: (from_account_id, to_account_id, amount, email) => request('/transfer', { method: 'POST', body: JSON.stringify({ from_account_id, to_account_id, amount, email }) }),

  // AI Agent & RAG Routes
  askPolicy: (question) => request('/rag/ask', { method: 'POST', body: JSON.stringify({ question }) }),
  chatAgent: (user_text, history, email) => request('/agent/chat', { method: 'POST', body: JSON.stringify({ user_text, history, email }) }),

  // Weather Routes
  getWeatherCities: () => request('/weather/cities'),
  getWeatherCity: (city) => request(`/weather/${encodeURIComponent(city)}`),
  askWeatherAgent: (user_text, history) => request('/weather/ask', {
    method: 'POST',
    body: JSON.stringify({ user_text, history }),
  }),

  // Live Crypto Routes
  getCryptoCurrencies: () => request('/crypto/currencies'),
  getCryptoAsset: (asset) => request(`/crypto/${encodeURIComponent(asset)}`),
  askCryptoAgent: (user_text, history) => request('/crypto/ask', {
    method: 'POST',
    body: JSON.stringify({ user_text, history }),
  }),
}