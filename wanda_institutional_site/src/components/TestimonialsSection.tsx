const TestimonialCard = ({ quote, author, role }: { quote: string, author: string, role: string }) => (
  <div className="bg-slate-800 p-8 rounded-lg shadow-xl text-center transform hover:scale-105 transition-transform duration-300">
    <p className="text-slate-300 italic text-lg mb-6">"{quote}"</p>
    <p className="text-white font-semibold text-xl">{author}</p>
    <p className="text-blue-400 text-sm">{role}</p>
  </div>
);

const TestimonialsSection = () => {
  const testimonials = [
    {
      quote: "DataQuery revolucionou a maneira como nossa equipe de marketing acessa e analisa dados de campanha. A interface de linguagem natural é incrivelmente intuitiva!",
      author: "Fernanda Costa",
      role: "Gerente de Marketing, AlphaTech"
    },
    {
      quote: "Nunca pensei que seria tão fácil obter insights complexos do nosso banco de dados. O SQL gerado é preciso e as visualizações são instantâneas. Recomendo!",
      author: "Ricardo Alves",
      role: "Analista de BI, BetaSolutions"
    },
    {
      quote: "A capacidade de criar dashboards personalizados rapidamente e o suporte para múltiplas fontes de dados tornaram o DataQuery uma ferramenta indispensável para nossa operação.",
      author: "Juliana Pereira",
      role: "Diretora de Operações, GammaCorp"
    }
  ];

  return (
    <section id="testimonials" className="py-16 bg-slate-900">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl font-bold text-center text-white mb-4">O Que Nossos Clientes Dizem</h2>
        <p className="text-center text-slate-400 mb-12 max-w-2xl mx-auto">
          Descubra como o DataQuery está ajudando empresas a transformarem dados em decisões estratégicas com facilidade e precisão.
        </p>
        <div className="grid md:grid-cols-1 lg:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <TestimonialCard key={index} quote={testimonial.quote} author={testimonial.author} role={testimonial.role} />
          ))}
        </div>
      </div>
    </section>
  );
};

export default TestimonialsSection;

