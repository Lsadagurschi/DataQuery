declare module 'next/font/google' {
  export function Inter(options: { subsets: string[] }): { className: string };
  // Adicione outras fontes do Google que você usa aqui, seguindo o mesmo padrão.
  // Exemplo: export function Roboto(options: { subsets: string[], weight: string | string[] }): { className: string };
}

declare module 'next/link' {
  import { AnchorHTMLAttributes, DetailedHTMLProps } from 'react';
  interface LinkProps extends DetailedHTMLProps<AnchorHTMLAttributes<HTMLAnchorElement>, HTMLAnchorElement> {
    href: string;
    replace?: boolean;
    scroll?: boolean;
    prefetch?: boolean;
    // Adicione outras props do Link conforme necessário
  }
  const Link: React.FC<LinkProps>;
  export default Link;
}

declare module 'next/image' {
  import { ImgHTMLAttributes, DetailedHTMLProps } from 'react';
  interface ImageProps extends DetailedHTMLProps<ImgHTMLAttributes<HTMLImageElement>, HTMLImageElement> {
    src: string;
    alt: string;
    width?: number | string;
    height?: number | string;
    fill?: boolean;
    // Adicione outras props do Image conforme necessário
  }
  const Image: React.FC<ImageProps>;
  export default Image;
}

