import { Routes, Route } from 'react-router-dom'
import { Navbar } from './components/Navbar'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Results from './pages/Results'
import History from './pages/History'
import Testing from './pages/Testing'
import NotFound from './pages/NotFound'

function App() {
    return (
        <>
            <Navbar />
            <main>
                <Routes>
                    <Route path="/" element={<Landing />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/results/:id" element={<Results />} />
                    <Route path="/history" element={<History />} />
                    <Route path="/testing" element={<Testing />} />
                    <Route path="*" element={<NotFound />} />
                </Routes>
            </main>
        </>
    )
}

export default App
