"use client"
import Link from "next/link"
import { usePathname } from "next/navigation" // Importa o hook para saber a URL atual
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

export function MainNavigation() {
  const pathname = usePathname() // Pega a rota atual (ex: "/" ou "/dashboard")
  const activeTab = pathname === "/dashboard" ? "progresso" : "exame"

  // Simplesmente definimos o idioma como português aqui.
  const t = {
    exame: "Exame",
    progresso: "Progresso",
  }

  return (
    <div className="sticky top-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
      <div className="container mx-auto px-4 py-3">
        <Card className="bg-card/50 border-border/50">
          <div className="flex rounded-lg overflow-hidden">
            <Button
              variant={activeTab === "exame" ? "default" : "ghost"}
              className={`flex-1 rounded-none border-0 font-medium transition-all duration-300 ${
                activeTab === "exame"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-transparent text-muted-foreground hover:text-foreground hover:bg-secondary/30"
              }`}
              asChild // Permite que o Botão se comporte como um Link
            >
              <Link href="/">{t.exame}</Link>
            </Button>
            <Button
              variant={activeTab === "progresso" ? "default" : "ghost"}
              className={`flex-1 rounded-none border-0 font-medium transition-all duration-300 ${
                activeTab === "progresso"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-transparent text-muted-foreground hover:text-foreground hover:bg-secondary/30"
              }`}
              asChild
            >
              <Link href="/dashboard">{t.progresso}</Link>
            </Button>
          </div>
        </Card>
      </div>
    </div>
  )
}