import { Link, useNavigate } from 'react-router-dom'
import { SignOut, ClockCounterClockwise, Gauge, Flask } from '@phosphor-icons/react'
import { useAuth } from '../lib/AuthContext'
import { supabase } from '../lib/supabase'

export function Navbar() {
    const { session } = useAuth()
    const navigate = useNavigate()

    const handleSignOut = async () => {
        await supabase.auth.signOut()
        navigate('/')
    }

    return (
        <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 md:px-12 bg-background/80 backdrop-blur-md border-b border-black/5">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2.5 transition-opacity hover:opacity-70">
                <div className="w-5 h-6 border-l-2 border-r-2 border-foreground/70 rounded-t-full flex items-center justify-center relative">
                    <div className="w-2.5 h-2.5 bg-foreground/70 rounded-full absolute bottom-0.5"></div>
                </div>
                <span className="text-3xl font-display text-foreground">GradGate</span>
            </Link>

            {/* Nav */}
            <nav className="hidden md:flex items-center gap-1">
                {!session ? (
                    <>
                        <Link
                            to="/login"
                            className="text-[13px] font-medium text-muted hover:text-foreground transition-colors px-4 py-2"
                        >
                            Sign In
                        </Link>
                        <Link
                            to="/login"
                            className="inline-flex items-center gap-2 bg-foreground text-background text-[13px] font-semibold rounded-sm px-5 py-2 hover:bg-foreground/90 transition-colors"
                        >
                            Get Started
                        </Link>
                    </>
                ) : (
                    <>
                        <Link
                            to="/history"
                            className="inline-flex items-center gap-1.5 text-[13px] font-medium text-muted hover:text-foreground transition-colors px-3 py-2"
                        >
                            <ClockCounterClockwise size={14} weight="regular" />
                            History
                        </Link>
                        <Link
                            to="/testing"
                            className="inline-flex items-center gap-1.5 text-[13px] font-medium text-muted hover:text-foreground transition-colors px-3 py-2"
                        >
                            <Flask size={14} weight="regular" />
                            Testing
                        </Link>
                        <Link
                            to="/dashboard"
                            className="inline-flex items-center gap-1.5 text-[13px] font-medium text-muted hover:text-foreground transition-colors px-3 py-2"
                        >
                            <Gauge size={14} weight="regular" />
                            Dashboard
                        </Link>
                        <div className="w-px h-4 bg-black/10 mx-1" />
                        <button
                            onClick={handleSignOut}
                            className="inline-flex items-center gap-1.5 text-[13px] font-medium text-muted hover:text-foreground transition-colors px-3 py-2"
                        >
                            <SignOut size={15} weight="regular" />
                            <span className="hidden lg:inline">Sign Out</span>
                        </button>
                    </>
                )}
            </nav>

            {/* Mobile */}
            <div className="md:hidden">
                {session ? (
                    <button onClick={handleSignOut} className="text-muted hover:text-foreground p-2">
                        <SignOut size={18} weight="regular" />
                    </button>
                ) : (
                    <Link to="/login" className="text-foreground text-[13px] font-medium">Sign In</Link>
                )}
            </div>
        </header>
    )
}
