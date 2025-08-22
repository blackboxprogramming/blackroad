import type { AppProps } from 'next/app';
import '@blackroad/ui/dist/styles.css';

export default function App({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />;
}
