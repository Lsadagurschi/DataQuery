const ContactSection = () => {
  return (
    <section id="contact" className="py-16 bg-slate-800">
      <div className="container mx-auto px-4 text-center">
        <h2 className="text-3xl font-bold text-white mb-4">Entre em Contato</h2>
        <p className="text-slate-400 mb-8 max-w-xl mx-auto">
          Tem alguma dúvida ou quer saber mais sobre como o DataQuery pode ajudar sua empresa? Nossa equipe está pronta para te atender.
        </p>
        <form className="max-w-lg mx-auto bg-slate-900 p-8 rounded-lg shadow-xl">
          <div className="mb-4">
            <label htmlFor="name" className="block text-slate-300 text-sm font-semibold mb-2 text-left">Nome Completo</label>
            <input type="text" id="name" name="name" className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500" required />
          </div>
          <div className="mb-4">
            <label htmlFor="email" className="block text-slate-300 text-sm font-semibold mb-2 text-left">Seu Melhor E-mail</label>
            <input type="email" id="email" name="email" className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500" required />
          </div>
          <div className="mb-6">
            <label htmlFor="message" className="block text-slate-300 text-sm font-semibold mb-2 text-left">Sua Mensagem</label>
            <textarea id="message" name="message" rows={4} className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500" required></textarea>
          </div>
          <button type="submit" className="w-full bg-teal-500 hover:bg-teal-600 text-white font-semibold px-6 py-3 rounded-md text-lg shadow-lg transition duration-300">
            Enviar Mensagem
          </button>
        </form>
      </div>
    </section>
  );
};

export default ContactSection;

