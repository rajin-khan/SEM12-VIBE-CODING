import { supabase } from '../lib/supabase'
import { GlassCard } from '../components/ui/GlassCard'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../lib/AuthContext'
import { GraduationCap } from '@phosphor-icons/react'

function GoogleG() {
    return (
        <svg viewBox="0 0 24 24" width="18" height="18" xmlns="http://www.w3.org/2000/svg">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
        </svg>
    )
}

export default function Login() {
    const { session, loading } = useAuth()

    if (loading) return (
        <div className="min-h-screen flex items-center justify-center bg-background">
            <p className="text-muted text-sm">Loading...</p>
        </div>
    )

    if (session) return <Navigate to="/dashboard" />

    const handleLogin = async () => {
        await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: { redirectTo: window.location.origin + '/dashboard' }
        })
    }

    return (
        <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-background">

            <div className="w-full max-w-sm" style={{ position: 'relative', zIndex: 10 }}>
                {/* Logo */}
                <div className="flex flex-col items-center mb-10 gap-4">
                    <div className="flex items-center gap-2.5">
                        <div className="w-5 h-6 border-l-2 border-r-2 border-foreground/70 rounded-t-full flex items-center justify-center relative">
                            <div className="w-2.5 h-2.5 bg-foreground/70 rounded-full absolute bottom-0.5"></div>
                        </div>
                        <span className="text-3xl font-display text-foreground">GradGate</span>
                    </div>
                    <div className="flex items-center gap-2 px-3 py-1 rounded-full border border-black/10 bg-white/50 backdrop-blur-sm">
                        <GraduationCap size={13} weight="thin" className="text-muted" />
                        <span className="text-[11px] font-medium text-muted tracking-wider uppercase">Degree Audit Platform</span>
                    </div>
                </div>

                <GlassCard className="flex flex-col gap-5 shadow-xl shadow-black/8">
                    <div className="text-center">
                        <h2 className="text-xl font-display text-foreground mb-1">Welcome back</h2>
                        <p className="text-muted text-sm">Sign in to access your audits and history.</p>
                    </div>

                    <div className="h-px bg-black/6" />

                    <button
                        onClick={handleLogin}
                        className="w-full flex items-center justify-center gap-3 bg-foreground text-background font-semibold py-3 px-6 rounded-sm hover:bg-foreground/90 transition-colors text-sm"
                    >
                        <GoogleG />
                        Continue with Google
                    </button>

                    <p className="text-center text-xs text-muted leading-relaxed">
                        By signing in, you agree to our<br />Terms of Service and Privacy Policy.
                    </p>
                </GlassCard>
            </div>
        </div>
    )
}
