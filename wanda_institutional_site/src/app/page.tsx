import Link from 'next/link';
import Image from 'next/image'; // Para usar se tivermos imagens locais para o herói ou funcionalidades

// Importando os componentes de seção
import HeroSection from '../components/HeroSection.tsx';
import FeaturesSection from '../components/FeaturesSection.tsx';
import TestimonialsSection from '../components/TestimonialsSection.tsx';
import PlansSection from '../components/PricingSection.tsx'; // Nome do arquivo é PricingSection.tsx

export default function HomePage() {
  return (
    <>
      <HeroSection />
      <FeaturesSection />
      <TestimonialsSection />
      <PlansSection />
      {/* Adicionar outras seções conforme necessário, como CTA final, etc. */}
    </>
  );
}

