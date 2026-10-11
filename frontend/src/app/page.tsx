import { ChatWindow } from "@/features/chat";

export default function Home() {
  return (
    <main className="h-screen w-screen flex flex-col overflow-hidden bg-background">
      <ChatWindow />
    </main>
  );
}
