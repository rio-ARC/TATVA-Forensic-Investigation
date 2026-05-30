import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import CaseFilePage from './pages/CaseFilePage'
import ReconstructionPage from './pages/ReconstructionPage'
import InvestigationPage from './pages/InvestigationPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/case/new" element={<CaseFilePage />} />
        <Route path="/reconstruction" element={<ReconstructionPage />} />
        <Route path="/investigation" element={<InvestigationPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
