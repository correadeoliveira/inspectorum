"use client"

import type React from "react"
import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Send, RefreshCw } from "lucide-react"
import Image from "next/image"
import { LoadingPopup } from "./loading-popup"

const API_URL = "http://localhost:5000/api";
const CHAT_STORAGE_KEY = 'exameChatState';

type ChatMode = 'exame' | 'rag';

interface Message {
  id: string;
  type: "user" | "ai";
  content: string;
  categoria?: string;
  timestamp: Date;
  isLoading?: boolean;
}

interface Question {
  id: string;
  categoria: string;
  texto: string;
}

interface ChatState {
    messages: Message[];
    isExamCompleted: boolean;
    chatMode: ChatMode;
    currentQuestion: Question | null;
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 p-2">
      <span className="h-2 w-2 rounded-full bg-current animate-bounce [animation-delay:-0.3s]"></span>
      <span className="h-2 w-2 rounded-full bg-current animate-bounce [animation-delay:-0.15s]"></span>
      <span className="h-2 w-2 rounded-full bg-current animate-bounce"></span>
    </div>
  )
}

export function ChatbotInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [isExamCompleted, setIsExamCompleted] = useState(false);
  const [showLoadingPopup, setShowLoadingPopup] = useState(false);
  const [chatMode, setChatMode] = useState<ChatMode>('exame');
  const pollingInterval = useRef<NodeJS.Timeout | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const t = {
    placeholderExame: "Digite sua resposta...",
    placeholderRag: "Tire suas dúvidas sobre a Doutrina...",
    send: "Enviar",
    analysisButton: "Ver Análise da IA",
    analysisLoading: "A IA está analisando suas respostas...",
    examCompleted: "Exame concluído!",
    startNewExam: "Iniciar Novo Exame",
  };

  useEffect(() => {
    const savedStateJSON = localStorage.getItem(CHAT_STORAGE_KEY);
    
    // ===== LÓGICA DE VERIFICAÇÃO DE DATA ADICIONADA =====
    if (savedStateJSON) {
      console.log("Estado do chat encontrado no localStorage. Verificando data...");
      const savedState: ChatState = JSON.parse(savedStateJSON);
      
      const lastMessageTimestamp = savedState.messages.length > 0
        ? new Date(savedState.messages[savedState.messages.length - 1].timestamp)
        : new Date(0); // Data muito antiga se não houver mensagens
      
      const today = new Date();

      // Compara se o dia, mês e ano são os mesmos
      if (lastMessageTimestamp.getDate() !== today.getDate() ||
          lastMessageTimestamp.getMonth() !== today.getMonth() ||
          lastMessageTimestamp.getFullYear() !== today.getFullYear()) 
      {
        console.log("A conversa salva é de um dia anterior. Limpando e começando de novo.");
        localStorage.removeItem(CHAT_STORAGE_KEY);
        fetchCurrentState(); // Pede um novo exame limpo ao backend
      } else {
        console.log("A conversa salva é de hoje. Carregando...");
        const formattedMessages = savedState.messages.map(msg => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
        setMessages(formattedMessages);
        setIsExamCompleted(savedState.isExamCompleted);
        setChatMode(savedState.chatMode);
        setCurrentQuestion(savedState.currentQuestion);
        setIsLoading(false);
      }
    } else {
      fetchCurrentState();
    }
    // =======================================================
  }, []);

  useEffect(() => {
    if (!isLoading && messages.length > 0) {
        const currentState: ChatState = {
            messages,
            isExamCompleted,
            chatMode,
            currentQuestion
        };
        localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(currentState));
    }
  }, [messages, isExamCompleted, chatMode, currentQuestion, isLoading]);

  const fetchCurrentState = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/exame/current-state`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      const formattedHistory: Message[] = Array.isArray(data.history) ? data.history.map((msg: Message) => ({ ...msg, timestamp: new Date(msg.timestamp) })) : [];
      setMessages(formattedHistory);
      if (data.status === "completed") {
        setIsExamCompleted(true);
        setCurrentQuestion(null);
        const hasAnalysis = formattedHistory.some(m => m.id === 'analysis-result' || m.id === 'rag-guidance');
        if (hasAnalysis) {
          setChatMode('rag');
        }
      } else if (data.status === "in_progress") {
        setIsExamCompleted(false);
        setChatMode('exame');
        setCurrentQuestion(data.next_question);
      }
    } catch (error) {
      console.error("FALHA CRÍTICA ao buscar o estado do exame:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = { id: Date.now().toString(), type: "user", content: inputValue.trim(), timestamp: new Date() };
    const submittedText = inputValue;
    setInputValue("");
    
    if (chatMode === 'exame' && currentQuestion) {
      setIsLoading(true);
      setMessages((prev) => [...prev, userMessage]);
      try {
        await fetch(`${API_URL}/exame/submit-answer`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question_id: currentQuestion.id, answer: submittedText }),
        });
        await fetchCurrentState();
      } catch (error) {
        console.error("Falha ao enviar resposta do exame:", error);
        setIsLoading(false);
      }
    } else if (chatMode === 'rag') {
      setIsLoading(true);
      const loadingMessage: Message = {
        id: 'rag-loading', type: 'ai', content: '', isLoading: true,
        categoria: 'Assistente de Doutrina', timestamp: new Date()
      };
      setMessages((prev) => [...prev, userMessage, loadingMessage]);

      try {
        const response = await fetch(`${API_URL}/rag/query`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: submittedText }),
        });
        const data = await response.json();
        const ragResponse: Message = {
            id: Date.now().toString() + "-rag", type: 'ai',
            content: data.answer ? `${data.answer}\n\nFontes: ${data.sources || 'N/A'}` : "Desculpe, não consegui processar sua pergunta.",
            categoria: 'Assistente de Doutrina', timestamp: new Date()
        };
        setMessages((prev) => [...prev.filter(m => m.id !== 'rag-loading'), ragResponse]);
      } catch(error) {
         console.error("Falha ao enviar pergunta RAG:", error);
         const errorResponse: Message = {
            id: Date.now().toString() + "-error", type: 'ai',
            content: "Ocorreu um erro ao processar sua pergunta. Por favor, tente novamente.",
            categoria: 'Erro do Sistema', timestamp: new Date()
        };
        setMessages((prev) => [...prev.filter(m => m.id !== 'rag-loading'), errorResponse]);
      } finally {
        setIsLoading(false);
      }
    }
  };
  
  const startStatusPolling = () => {
    if (pollingInterval.current) clearInterval(pollingInterval.current);
    pollingInterval.current = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/dashboard/status`);
        const statusData = await response.json();
        if (statusData.status === "idle") {
          console.log("Análise em background concluída!");
          if (pollingInterval.current) clearInterval(pollingInterval.current);
          setShowLoadingPopup(false);
        } else {
          console.log("Backend ainda processando a análise de progresso...");
        }
      } catch (err) {
        console.error("Erro no polling de status:", err);
        if (pollingInterval.current) clearInterval(pollingInterval.current);
        setShowLoadingPopup(false);
      }
    }, 5000);
  };

  const handleAnalysis = async () => {
    setShowLoadingPopup(true);
    const analysisMessage: Message = { id: 'analysis-loading', type: "ai", content: t.analysisLoading, timestamp: new Date() };
    setMessages((prev) => [...prev, analysisMessage]);
    try {
      const response = await fetch(`${API_URL}/exame/analyze`, { method: 'POST' });
      const data = await response.json();
      const finalAnalysis: Message = { id: 'analysis-result', type: "ai", content: data.analysis, timestamp: new Date() };
      const guidanceMessage: Message = {
          id: 'rag-guidance', type: 'ai',
          content: 'Análise concluída. A partir de agora, você pode me fazer perguntas sobre a fé e a Doutrina com base nos documentos.',
          categoria: 'Modo de Consulta Ativado', timestamp: new Date()
      };
      setMessages((prev) => [...prev.filter(m => m.id !== 'analysis-loading'), finalAnalysis, guidanceMessage]);
      setIsExamCompleted(true);
      setChatMode('rag');
      startStatusPolling();
    } catch (error) {
      console.error("Falha ao obter análise:", error);
      setShowLoadingPopup(false);
    }
  };

  const handleStartNewExam = async () => {
    localStorage.removeItem(CHAT_STORAGE_KEY);
    setIsLoading(true);
    setMessages([]);
    setIsExamCompleted(false);
    setChatMode('exame');
    try {
      await fetch(`${API_URL}/exame/start-new`, { method: 'POST' });
      await fetchCurrentState();
    } catch (error) {
      console.error("Falha ao iniciar novo exame:", error);
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);
  
  return (
    <>
      <LoadingPopup isOpen={showLoadingPopup} statusText={t.analysisLoading} />
      <div className="flex flex-col h-full bg-card/20 rounded-lg border border-border">
        <div className="flex-1 overflow-y-auto space-y-6 p-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex gap-3 ${message.type === "user" ? "justify-end" : "items-start justify-start"}`}>
              {message.type === "ai" && (
                <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center">
                  <Image src="/logo.png" alt="AI Avatar" width={28} height={28} className="object-contain" />
                </div>
              )}
              <Card className={`max-w-[85%] ${message.type === "user" ? "bg-primary text-primary-foreground" : "bg-card border-border"}`}>
                <CardContent className="p-3">
                  {message.type === "ai" && (
                    <div className="text-xs text-amber-400 mb-2 font-semibold tracking-wide">
                      {message.categoria || "Exame de Consciência"}
                    </div>
                  )}
                  {message.isLoading 
                    ? <TypingIndicator /> 
                    : <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                  }
                  <div className="text-xs opacity-60 mt-2 text-right">{message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</div>
                </CardContent>
              </Card>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        <div className="border-t border-border/50 p-4 bg-background/50 backdrop-blur-sm rounded-b-lg">
          {isExamCompleted ? (
            chatMode === 'rag' ? (
              <div className="flex gap-2 items-center bg-input/50 border border-border rounded-full p-2 focus-within:ring-2 focus-within:ring-primary/50 transition-all">
                <Input value={inputValue} onChange={(e) => setInputValue(e.target.value)} onKeyPress={handleKeyPress} placeholder={t.placeholderRag} className="flex-1 bg-transparent border-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-foreground" disabled={isLoading}/>
                <Button onClick={handleSendMessage} disabled={isLoading || !inputValue.trim()} size="icon" className="rounded-full flex-shrink-0 bg-primary hover:bg-primary/90"><Send className="w-4 h-4" /><span className="sr-only">{t.send}</span></Button>
              </div>
            ) : (
              <div className="flex gap-2 justify-center">
                <Button onClick={handleAnalysis} disabled={isLoading}>{t.analysisButton}</Button>
                <Button onClick={handleStartNewExam} disabled={isLoading} variant="outline"><RefreshCw className="w-4 h-4 mr-2" />{t.startNewExam}</Button>
              </div>
            )
          ) : (
            <div className="flex gap-2 items-center bg-input/50 border border-border rounded-full p-2 focus-within:ring-2 focus-within:ring-primary/50 transition-all">
              <Input value={inputValue} onChange={(e) => setInputValue(e.target.value)} onKeyPress={handleKeyPress} placeholder={t.placeholderExame} className="flex-1 bg-transparent border-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-foreground" disabled={isLoading}/>
              <Button onClick={handleSendMessage} disabled={isLoading || !inputValue.trim()} size="icon" className="rounded-full flex-shrink-0 bg-primary hover:bg-primary/90"><Send className="w-4 h-4" /><span className="sr-only">{t.send}</span></Button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}