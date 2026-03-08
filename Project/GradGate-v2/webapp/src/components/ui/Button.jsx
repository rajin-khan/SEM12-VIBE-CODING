import { cn } from "../../lib/utils"

export function Button({ className, variant = "primary", children, ...props }) {
    const baseStyles = "inline-flex items-center justify-center font-medium transition-all focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50"

    const variants = {
        primary: "bg-foreground text-background hover:bg-foreground/90 rounded-sm px-6 py-3 text-sm",
        glass: "bg-black/5 border border-black/10 text-foreground hover:bg-black/8 rounded-sm px-6 py-3 text-sm",
        ghost: "text-muted hover:text-foreground transition-colors"
    }

    return (
        <button className={cn(baseStyles, variants[variant], className)} {...props}>
            {children}
        </button>
    )
}
