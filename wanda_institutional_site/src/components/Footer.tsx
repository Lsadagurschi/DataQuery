import Link from 'next/link';

const Footer = () => {
  return (
    <footer className="bg-slate-800 text-slate-300 p-8 mt-12">
      <div className="container mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
        <div>
          <h3 className="text-xl font-semibold text-blue-400 mb-3">Wanda</h3>
          <p className="text-sm">Desvende o poder dos seus dados com linguagem natural. Consulte seus bancos de dados e obtenha insights instantâneos.</p>
        </div>
        <div>
          <h4 className="text-lg font-semibold text-white mb-3">Links Úteis</h4>
          <ul className="space-y-2 text-sm">
            <li><Link href="#funcionalidades" className="hover:text-blue-300">Funcionalidades</Link></li>
            <li><Link href="#planos" className="hover:text-blue-300">Planos</Link></li>
            <li><Link href="/blog" className="hover:text-blue-300">Blog</Link></li>
            <li><Link href="/contato" className="hover:text-blue-300">Contato</Link></li>
            <li><Link href="/termos" className="hover:text-blue-300">Termos de Serviço</Link></li>
            <li><Link href="/privacidade" className="hover:text-blue-300">Política de Privacidade</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="text-lg font-semibold text-white mb-3">Contato</h4>
          <p className="text-sm">Email: contato@wanda.ai</p>
          {/* Adicionar mais informações de contato ou links de redes sociais aqui */}
        </div>
      </div>
      <div className="mt-8 pt-8 border-t border-slate-700 text-center text-sm">
        <p>&copy; {new Date().getFullYear()} Wanda. Todos os direitos reservados.</p>
      </div>
    </footer>
  );
};

export default Footer;

