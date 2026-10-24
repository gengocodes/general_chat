import { PromptCategory } from "../types/chat.types";

export const ASSISTANT_NAME = "Gengo";

export const PROMPT_CATEGORIES: readonly PromptCategory[] = [
  {
    id: "capabilities",
    label: "Gengo's capabilities",
    icon: "sparkles",
    items: [
      {
        label: "Explore what Gengo can do",
        prompt:
          "Hi Gengo! Can you give me an overview of your capabilities, the tools you have access to, and how you can help me?",
      },
      {
        label: "Understand Gengo's microservice architecture",
        prompt:
          "How is Gengo architected behind the scenes, and how do your chat, storage, and document services work together?",
      },
      {
        label: "Learn how file privacy and 24-hour auto-deletion work",
        prompt:
          "How does Gengo handle uploaded files, security, and the 24-hour automatic retention policy?",
      },
      {
        label: "See examples of tasks we can collaborate on",
        prompt:
          "What are the most impactful engineering, writing, or document workflows we can tackle together right now?",
      },
    ],
  },
  {
    id: "documents",
    label: "Document tools",
    icon: "files",
    items: [
      {
        label: "Convert a Word (.docx) document into a PDF",
        prompt:
          "I want to convert a Microsoft Word (.docx) file into a clean PDF document. Please convert the attached DOCX file to PDF.",
      },
      {
        label: "Convert a PDF document into an editable Word (.docx) file",
        prompt:
          "I need to turn a PDF into an editable Microsoft Word (.docx) document. Please convert the attached PDF file to DOCX.",
      },
      {
        label: "Summarize and extract key action items from a document",
        prompt:
          "Could you review my document, summarize its core points, and extract a structured list of action items?",
      },
      {
        label: "Proofread and refine a technical report or contract",
        prompt:
          "Help me polish a technical document for clarity, tone, and structure. Ask me 1–2 questions about the target audience first.",
      },
    ],
  },
  {
    id: "code",
    label: "Code & Architecture",
    icon: "code",
    items: [
      {
        label: "Design a system using Strict Clean Architecture",
        prompt:
          "Help me design a backend feature following Strict Clean Architecture (Domain, Application, Infrastructure, Presentation). Ask me about the domain requirements to get started.",
      },
      {
        label: "Audit code for code smells, false optionals, and security",
        prompt:
          "I'd like you to review a piece of code for Clean Architecture boundaries, false optionals, primitive obsession, and security vulnerabilities.",
      },
      {
        label: "Design cloud-native microservices for Google Cloud Run",
        prompt:
          "Help me architect a stateless, secure microservice deployment on Google Cloud Run with internal service-to-service authentication.",
      },
      {
        label: "Debug a complex full-stack TypeScript or Python issue",
        prompt:
          "I'm running into a bug in my stack. Walk me through a systematic root-cause analysis once I share the error or traceback.",
      },
    ],
  },
  {
    id: "write",
    label: "Write",
    icon: "pen",
    items: [
      {
        label: "Write engineering documentation & architecture guides",
        prompt:
          "Help me write clear, production-grade engineering documentation with Mermaid architecture diagrams. Ask me 1–2 questions about the service first.",
      },
      {
        label: "Draft a technical RFC or system design proposal",
        prompt:
          "Could you help me draft a structured engineering RFC covering context, trade-offs, security, and rollout plan?",
      },
      {
        label: "Craft compelling product copy or release notes",
        prompt:
          "Help me write crisp, high-impact release notes or product copy. If you need more context from me, ask 1–2 key questions right away.",
      },
      {
        label: "Write a clear executive summary for stakeholders",
        prompt:
          "Help me distill a complex technical initiative into a concise executive summary with clear outcomes and milestones.",
      },
    ],
  },
  {
    id: "brainstorm",
    label: "Brainstorm",
    icon: "lightbulb",
    items: [
      {
        label: "Brainstorm high-leverage AI agent features",
        prompt:
          "Let's brainstorm practical, high-leverage AI agent capabilities and tool integrations we could build next.",
      },
      {
        label: "Evaluate technical trade-offs between two approaches",
        prompt:
          "Help me compare two architectural approaches across cost, latency, maintainability, and security.",
      },
      {
        label: "Plan a step-by-step product MVP roadmap",
        prompt:
          "Help me break down a new product idea into a lean, shippable MVP roadmap with clear engineering milestones.",
      },
    ],
  },
];
