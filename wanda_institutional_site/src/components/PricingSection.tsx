import Link from 'next/link';

const PlanCard = ({ name, price, features, ctaText, primary = false }: { name: string, price: string, features: string[], ctaText: string, primary?: boolean }) => (
  <div className={`border ${primary ? 'border-blue-500 bg-slate-800' : 'border-slate-700 bg-slate-800/50'} p-8 rounded-lg shadow-xl flex flex-col`}>
    <h3 className={`text-2xl font-bold ${primary ? 'text-blue-400' : 'text-white'} mb-4`}>{name}</h3>
    <p className={`text-4xl font-extrabold ${primary ? 'text-white' : 'text-slate-300'} mb-6`}>{price}<span className="text-base font-normal text-slate-400">/mês</span></p>
    <ul className="space-y-3 text-slate-400 mb-8 flex-grow">
      {features.map((feature, index) => (
        <li key={index} className="flex items-center">
          <svg className={`w-5 h-5 ${primary ? 'text-blue-500' : 'text-teal-500'} mr-2`} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"></path>
          </svg>
          {feature}
        </li>
      ))}
    </ul>
    <Link href="/signup" className={`w-full text-center font-semibold py-3 rounded-md transition duration-300 ${primary ? 'bg-blue-500 hover:bg-blue-600 text-white shadow-lg' : 'bg-slate-700 hover:bg-slate-600 text-slate-200'}`}>
      {ctaText}
    </Link>
  </div>
);

const PricingSection = () => {
  const plans = [
    {
      name: "Básico",
      price: "R$199",
      features: [
        "Até 3 usuários",
        "100 consultas/mês",
        "1 conexão de banco de dados",
        "Suporte por e-mail"
      ],
      ctaText: "Assinar Plano Básico"
    },
    {
      name: "Profissional",
      price: "R$499",
      features: [
        "Até 10 usuários",
        "500 consultas/mês",
        "3 conexões de banco de dados",
        "Suporte prioritário",
        "Exportação em múltiplos formatos"
      ],
      ctaText: "Assinar Plano Profissional",
      primary: true
    },
    {
      name: "Empresarial",
      price: "R$999",
      features: [
        "Usuários ilimitados",
        "Consultas ilimitadas",
        "Conexões ilimitadas",
        "Suporte 24/7",
        "API avançada",
        "Treinamento personalizado"
      ],
      ctaText: "Assinar Plano Empresarial"
    }
  ];

  return (
    <section id="pricing" className="py-16 bg-slate-900">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl font-bold text-center text-white mb-4">Planos Flexíveis para Todos os Tamanhos</h2>
        <p className="text-center text-slate-400 mb-12 max-w-2xl mx-auto">
          Escolha o plano DataQuery que melhor se adapta às suas necessidades e comece a transformar seus dados em decisões hoje mesmo.
        </p>
        <div className="grid md:grid-cols-1 lg:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {plans.map((plan, index) => (
            <PlanCard key={index} {...plan} />
          ))}
        </div>
      </div>
    </section>
  );
};

export default PricingSection;

