import { useEffect, useState } from "react";
import { defaultProgramImageUrl } from "../config/assets";

interface ProgramImageProps {
  src?: string | null;
  alt: string;
  className?: string;
  loading?: "eager" | "lazy";
}

export function ProgramImage({
  src,
  alt,
  className,
  loading = "lazy",
}: ProgramImageProps) {
  const preferredSource = src || defaultProgramImageUrl;
  const [currentSource, setCurrentSource] = useState(preferredSource);

  useEffect(() => {
    setCurrentSource(preferredSource);
  }, [preferredSource]);

  return (
    <img
      className={className}
      src={currentSource}
      alt={alt}
      loading={loading}
      onError={() => {
        if (currentSource !== defaultProgramImageUrl) {
          setCurrentSource(defaultProgramImageUrl);
        }
      }}
    />
  );
}
