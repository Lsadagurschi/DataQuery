import { BarChart3, MessageSquareText, Share2, ShieldCheck } from 'lucide-react';

const FeatureCard = ({ icon: Icon, title, description }: { icon: React.ElementType, title: string, description: string }) => (
  <div className="bg-slate-800 p-6 rounded-lg shadow-lg hover:shadow-blue-500/30 transition-shadow duration-300">
    <div className="flex items-center justify-center w-12 h-12 bg-blue-500 rounded-full mb-4">
      <Icon className="w-6 h-6 text-white" />
    </div>
    <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
    <p className="text-slate-400 text-sm leading-relaxed">{description}</p>
  </div>
);

const FeaturesSection = () => {
  const features = [
    {
      icon: MessageSquareText,
      title: "Consultas em Linguagem Natural",
      description: "Transforme perguntas complexas em consultas SQL precisas sem escrever uma única linha de código. Intuitivo e poderoso."
    },
    {
      icon: BarChart3,
      title: "Visualizações Dinâmicas",
      description: "Gere gráficos e tabelas interativas automaticamente para entender seus dados de forma visual e clara. Crie dashboards personalizados."
    },
    {
      icon: Share2,
      title: "Integração e Compartilhamento",
      description: "Conecte-se facilmente aos seus bancos de dados e compartilhe insights com sua equipe através de relatórios e dashboards exportáveis."
    },
    {
      icon: ShieldCheck,
      title: "Segurança e Conformidade",
      description: "Seus dados protegidos com as melhores práticas de segurança e em conformidade com a LGPD, garantindo tranquilidade."
    }
  ];

  return (
    <section id="features" className="py-16 bg-slate-900">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl font-bold text-center text-white mb-4">Principais Funcionalidades</h2>
        <p className="text-center text-slate-400 mb-12 max-w-2xl mx-auto">
          DataQuery oferece um conjunto completo de ferramentas para transformar a maneira como você interage e extrai valor dos seus dados.
        </p>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <FeatureCard key={index} icon={feature.icon} title={feature.title} description={feature.description} />
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;

