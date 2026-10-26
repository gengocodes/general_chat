import React, { useId } from "react";
import { cn } from "@/shared/lib/utils";

interface GengoLogoProps {
  className?: string;
}

export const GengoLogo: React.FC<GengoLogoProps> = ({ className }) => {
  const uid = useId();
  const rimId = `gengo-rim-${uid}`;
  const bgId = `gengo-bg-${uid}`;

  return (
    <svg
      viewBox="0 0 120 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("shrink-0 select-none", className)}
      aria-label="Gengo logo"
      role="img"
    >
      <defs>
        <linearGradient
          id={rimId}
          x1="0"
          y1="0"
          x2="120"
          y2="120"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0%" stopColor="#71717A" />
          <stop offset="50%" stopColor="#3F3F46" />
          <stop offset="100%" stopColor="#18181B" />
        </linearGradient>
        <linearGradient
          id={bgId}
          x1="20"
          y1="15"
          x2="100"
          y2="105"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0%" stopColor="#52525B" />
          <stop offset="100%" stopColor="#27272A" />
        </linearGradient>
      </defs>
      <circle
        cx="60"
        cy="60"
        r="57"
        fill={`url(#${rimId})`}
        stroke="#52525B"
        strokeWidth="2"
      />
      <circle
        cx="60"
        cy="60"
        r="49"
        fill={`url(#${bgId})`}
        stroke="#E4E4E7"
        strokeWidth="2.5"
      />
      <path
        d="M44 34H82L74 46H48L40 54V66L48 74H72V62H58L64 52H86V78L74 88H42L28 74V48L44 34Z"
        fill="#18181B"
        transform="translate(2, 3)"
      />
      <path
        d="M44 34H82L74 46H48L40 54V66L48 74H72V62H58L64 52H86V78L74 88H42L28 74V48L44 34Z"
        fill="#F4F4F5"
      />
      <path d="M58 62H86V78L74 88H56L68 74V62H58Z" fill="#A1A1AA" />
    </svg>
  );
};
