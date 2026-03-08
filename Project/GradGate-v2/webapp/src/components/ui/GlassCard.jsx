import { cn } from "../../lib/utils"

export function GlassCard({ className, children, ...props }) {
    return (
        <div className={cn("glass-panel rounded-2xl p-6 md:p-8", className)} {...props}>
            {children}
        </div>
    )
}
