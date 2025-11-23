import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { UploadPage } from './pages/UploadPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<UploadPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
