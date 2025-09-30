import { ChatbotInterface } from "@/components/chatbot-interface";
import Image from "next/image";

export default function ExamePage() {
  return (
    // MUDANÇA AQUI: Trocamos 'h-full' por 'flex-1' para que a grade se estique
    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6 flex-1">
      
      {/* Coluna da Esquerda: Barra Lateral Fixa */}
      <aside className="hidden md:flex flex-col space-y-4 p-6 bg-card/30 rounded-lg border border-border">
        <div className="flex flex-col items-center gap-4 text-center">
          <Image src="/logo.png" alt="Logo" width={64} height={64} className="object-contain" />
          <h1 className="text-xl font-bold text-foreground">Exame de Consciência</h1>
        </div>
        <div className="border-t border-border/50 my-4"></div>
        <div className="text-sm text-muted-foreground space-y-3">
          <p>Este é um momento de reflexão sincera e oração.</p>
          <p>Responda a cada pergunta com o coração aberto, buscando a verdade sobre suas ações, pensamentos e omissões. O objetivo não é o julgamento, mas o encontro com a misericórdia e o caminho para a conversão.</p>
          <p>Suas respostas são privadas e servirão de base para a análise final gerada pela IA, que oferecerá uma perspectiva para seu crescimento espiritual.</p>
        </div>
      </aside>

      {/* Coluna da Direita: Interface do Chat */}
      <div className="md:col-span-2 lg:col-span-3 h-full">
        <ChatbotInterface />
      </div>
    </div>
  );
}