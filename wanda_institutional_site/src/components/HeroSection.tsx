import Link from 'next/link';

const HeroSection = () => {
  return (
    <section className="bg-slate-900 text-white py-20">
      <div className="container mx-auto grid md:grid-cols-2 gap-8 items-center px-4">
        <div className="md:pr-8">
          <h1 className="text-4xl md:text-5xl font-bold mb-6 leading-tight">
            Desvende o Poder dos Seus Dados com Linguagem Natural
          </h1>
          <p className="text-lg text-slate-300 mb-8">
            Editorelcdul contembin cutuãnt duta tresonmito. Oioduls elhil ejl telege emvi pøjueterlo illa lual esur a minac patisiue dra. elil.
          </p>
          <Link href="#pricing" className="bg-teal-500 hover:bg-teal-600 text-white font-semibold px-8 py-3 rounded-md text-lg shadow-lg transition duration-300">
            Comece seu Teste Gratuito
          </Link>
        </div>
        <div className="mt-8 md:mt-0">
          {/* Placeholder for an illustrative image/graphic related to data/AI/dashboards */}
          <img src="https://placehold.co/600x400/1e293b/94a3b8?text=Visualiza%C3%A7%C3%A3o+de+Dados" alt="DataQuery Platform Illustration" className="rounded-lg shadow-xl" />
        </div>
      </div>
    </section>
  );
};

export default HeroSection;

