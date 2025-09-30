"use client"

import { AlertDialog, AlertDialogContent } from "@/components/ui/alert-dialog"
import Image from "next/image"
import { Loader2 } from "lucide-react"

interface LoadingPopupProps {
  isOpen: boolean;
  statusText: string; // <-- Propriedade adicionada
}

export function LoadingPopup({ isOpen, statusText }: LoadingPopupProps) {
  return (
    <AlertDialog open={isOpen}>
      <AlertDialogContent className="max-w-sm text-center border-amber-800/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex flex-col items-center justify-center gap-4 p-6">
          <Image src="/logo.png" alt="Logo" width={80} height={80} className="object-contain" />
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-foreground">Inspectorum</h2>
            <p className="text-lg text-muted-foreground">Exame de Consciência</p>
          </div>
          <div className="w-16 h-16 my-4">
            <Loader2 className="w-full h-full text-amber-500 animate-spin" />
          </div>
          {/* O texto agora é dinâmico */}
          <p className="text-sm text-amber-400">
            {statusText}
          </p>
        </div>
      </AlertDialogContent>
    </AlertDialog>
  );
}