interface IconProps {
  size?: number;
}

export function BrowserIcon({ size = 14 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor">
      <path d="M2 3a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v2H2V3zm0 3h12v7a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V6zm2 2v1h2V8H4zm3 0v1h2V8H7zm3 0v1h2V8h-2z" />
    </svg>
  );
}

export function CrisprIcon({ size = 14 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor">
      <path d="M8 1a1 1 0 0 1 1 1v1.06a4.5 4.5 0 0 1 3.44 3.44H13.5a1 1 0 1 1 0 2h-1.06a4.5 4.5 0 0 1-3.44 3.44V13a1 1 0 1 1-2 0v-1.06A4.5 4.5 0 0 1 3.56 8.5H2.5a1 1 0 0 1 0-2h1.06A4.5 4.5 0 0 1 7 3.06V2a1 1 0 0 1 1-1zm0 5a2 2 0 1 0 0 4 2 2 0 0 0 0-4z" />
    </svg>
  );
}

export function SimulationIcon({ size = 14 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor">
      <path d="M3 2h10v2H3V2zm0 4h6v2H3V6zm0 4h10v2H3v-2zm0 3h7v2H3v-2zM11 6l3 2-3 2V6z" />
    </svg>
  );
}

export function SequencingIcon({ size = 14 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor">
      <path d="M2 3h1v10H2V3zm2 0h1v6H4V3zm3 0h1v10H7V3zm3 0h1v4h-1V3zm3 0h1v10h-1V3z" />
    </svg>
  );
}