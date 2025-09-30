"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { TrendingDown, TrendingUp, MessageSquare, AlertTriangle } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"

interface DashboardData {
  chartData: { day: string; sins: number; virtues: number }[];
  summary: {
    totalSessions: number;
    dailyImprovement: number;
    consecutiveDays: number;
  };
}

export function ProgressDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch("http://localhost:5000/api/dashboard/progress");
        if (!response.ok) {
          throw new Error(`Erro na API: ${response.statusText}`);
        }
        const fetchedData: DashboardData = await response.json();
        setData(fetchedData);
      } catch (err) {
        console.error("Falha ao buscar dados do dashboard:", err);
        setError("Não foi possível carregar os dados de progresso. Verifique o console do backend para mais detalhes.");
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  const t = {
    title: "Progresso Espiritual",
    sinReduction: "Redução de Pecados",
    virtueEvolution: "Evolução das Virtudes",
    thisWeek: "Esta Semana",
  };

  if (isLoading) { /* ... (bloco do skeleton sem alterações) ... */ }
  if (error) { /* ... (bloco de erro sem alterações) ... */ }
  if (!data || !data.summary || !data.chartData) {
    return <p>Ainda não há dados de progresso para exibir. Complete um exame primeiro.</p>;
  }

  return (
    <div className="w-full space-y-6">
      <div className="text-center mb-6">
        <h1 className="text-3xl font-bold text-foreground">{t.title}</h1>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sin Reduction Chart */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-card-foreground"><TrendingDown className="w-5 h-5 text-red-600" />{t.sinReduction}</CardTitle>
            <p className="text-sm text-muted-foreground">{t.thisWeek}</p>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#4a4a4a" />
                  <XAxis dataKey="day" stroke="#8B7355" fontSize={12} />
                  <YAxis stroke="#8B7355" fontSize={12} />
                  <Tooltip contentStyle={{ backgroundColor: "#2a1810", border: "1px solid #8B7355" }} />
                  <Line type="monotone" dataKey="sins" name="Pecados" stroke="#DC2626" strokeWidth={3} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Virtue Evolution Chart */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-card-foreground"><TrendingUp className="w-5 h-5 text-amber-600" />{t.virtueEvolution}</CardTitle>
            <p className="text-sm text-muted-foreground">{t.thisWeek}</p>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#4a4a4a" />
                  <XAxis dataKey="day" stroke="#8B7355" fontSize={12} />
                  <YAxis stroke="#8B7355" fontSize={12} />
                  <Tooltip contentStyle={{ backgroundColor: "#2a1810", border: "1px solid #8B7355" }} />
                  <Line type="monotone" dataKey="virtues" name="Virtudes" stroke="#D4AF37" strokeWidth={3} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Cards de Resumo */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total de Sessões</p>
                <p className="text-2xl font-bold text-card-foreground">{data.summary.totalSessions}</p>
              </div>
              <MessageSquare className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Melhoria Diária nos Pecados</p>
                <p className="text-2xl font-bold text-green-500">{data.summary.dailyImprovement >= 0 ? '+' : ''}{data.summary.dailyImprovement}%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Dias Consecutivos</p>
                <p className="text-2xl font-bold text-card-foreground">{data.summary.consecutiveDays}</p>
              </div>
               <TrendingDown className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}