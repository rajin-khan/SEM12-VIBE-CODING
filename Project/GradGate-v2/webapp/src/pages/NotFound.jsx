import { Link } from 'react-router-dom'
import { ArrowLeft } from '@phosphor-icons/react'

export default function NotFound() {
    return (
        <div className="min-h-screen flex flex-col items-center justify-center text-center px-6 bg-background">
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-amber-100/60 blur-[140px]" />
            </div>

            <p className="text-[10rem] font-display text-foreground/5 leading-none select-none">404</p>

            <div className="-mt-8">
                <h1 className="text-4xl font-display text-foreground mb-3">Page not found</h1>
                <p className="text-muted text-sm max-w-sm mx-auto mb-8">
                    This page doesn't exist or may have been moved.
                </p>
                <Link
                    to="/"
                    className="inline-flex items-center gap-2 text-sm text-muted hover:text-foreground transition-colors border border-black/10 px-5 py-2.5 rounded-lg hover:border-black/20"
                >
                    <ArrowLeft size={14} weight="regular" />
                    Back to Home
                </Link>
            </div>
        </div>
    )
}
