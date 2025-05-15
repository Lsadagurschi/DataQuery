'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Menu, X } from 'lucide-react';

const Header = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <header className="bg-slate-900 text-white p-4 shadow-md sticky top-0 z-50">
      <nav className="container mx-auto flex justify-between items-center">
        <Link href="/" className="text-2xl font-bold text-blue-400">
          DataQuery
        </Link>
        {/* Desktop Menu */}
        <div className="hidden md:flex space-x-4 items-center">
          <Link href="#features" className="hover:text-blue-300">Funcionalidades</Link>
          <Link href="#pricing" className="hover:text-blue-300">Planos</Link>
          <Link href="/blog" className="hover:text-blue-300">Blog</Link>
          <Link href="#contact" className="hover:text-blue-300">Contato</Link>
          <Link href="/login" className="bg-blue-500 hover:bg-blue-600 px-4 py-2 rounded-md text-sm font-medium">Login</Link>
        </div>
        {/* Mobile Menu Button */}
        <div className="md:hidden">
          <button onClick={() => setIsOpen(!isOpen)} className="text-white focus:outline-none">
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </nav>
      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden mt-4 bg-slate-900">
          <Link href="#features" className="block py-2 px-4 text-sm hover:bg-slate-700 rounded" onClick={() => setIsOpen(false)}>Funcionalidades</Link>
          <Link href="#pricing" className="block py-2 px-4 text-sm hover:bg-slate-700 rounded" onClick={() => setIsOpen(false)}>Planos</Link>
          <Link href="/blog" className="block py-2 px-4 text-sm hover:bg-slate-700 rounded" onClick={() => setIsOpen(false)}>Blog</Link>
          <Link href="#contact" className="block py-2 px-4 text-sm hover:bg-slate-700 rounded" onClick={() => setIsOpen(false)}>Contato</Link>
          <Link href="/login" className="block py-2 px-4 text-sm bg-blue-500 hover:bg-blue-600 rounded mt-2 mb-2 font-medium">Login</Link>
        </div>
      )}
    </header>
  );
};

export default Header;

