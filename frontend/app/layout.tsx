"use client"

import { useState, useEffect } from "react"
import { Inter } from "next/font/google";
import "./globals.css";
import { MainNavigation } from "@/components/main-navigation";
import { LoadingPopup } from "@/components/loading-popup";
import { AlertTriangle } from "lucide-react";

const inter = Inter({ subsets: ["latin"] });

function SystemError({ errors }: { errors: string[] }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen text-center p-4">
      <AlertTriangle className="h-16 w-16 text-destructive mb-4" />
      <h1 className="text-2xl font-bold text-destructive mb-2">Erro de Configuração do Sistema</h1>
      <p className="text-muted-foreground mb-6 max-w-lg">
        Não foi possível iniciar a aplicação. Por favor, verifique os seguintes problemas no seu ambiente local:
      </p>
      <div className="bg-card/50 p-4 rounded-lg border border-border text-left">
        <ul className="list-disc list-inside space-y-2">
          {errors.map((error, index) => (
            <li key={index} className="text-sm">{error}</li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // NOVO: Usamos um estado de "máquina de estados" para mais controle
  const [systemStatus, setSystemStatus] = useState<'checking' | 'ready' | 'error'>('checking');
  const [systemError, setSystemError] = useState<string[] | null>(null);

  useEffect(() => {
    const checkSystem = async () => {
      try {
        const response = await fetch("http://localhost:5000/api/system/health");
        const data = await response.json();
        
        if (response.ok && data.status === 'ok') {
          // Deu tudo certo, o sistema está pronto
          setSystemStatus('ready');
        } else {
          // A API retornou um erro
          setSystemError(data.errors || ["Ocorreu um erro desconhecido no backend."]);
          setSystemStatus('error');
        }
      } catch (err) {
        // A API nem sequer respondeu
        console.error("Falha ao conectar com o backend:", err);
        setSystemError(["Não foi possível conectar ao servidor do backend. Verifique se ele está rodando."]);
        setSystemStatus('error');
      }
    };

    // Adiciona um pequeno delay para garantir que a tela de loading seja visível
    setTimeout(() => {
      checkSystem();
    }, 500); // Meio segundo

  }, []); // Roda apenas uma vez

  // O HTML agora é renderizado com base no estado do sistema
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body className={inter.className}>
        {systemStatus === 'checking' && (
          <LoadingPopup 
            isOpen={true} 
            statusText="Verificando o sistema e as dependências..." 
          />
        )}

        {systemStatus === 'error' && systemError && (
          <SystemError errors={systemError} />
        )}

        {systemStatus === 'ready' && (
          <div className="flex min-h-screen w-full flex-col">
            <MainNavigation />
            <main className="flex flex-col flex-1 container mx-auto py-6">
              {children}
            </main>
          </div>
        )}
      </body>
    </html>
  );
}