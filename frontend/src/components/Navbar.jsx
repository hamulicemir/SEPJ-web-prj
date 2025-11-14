import { Link } from "react-router-dom";
import { Navbar, NavbarBrand, NavbarCollapse, NavbarLink, NavbarToggle } from "flowbite-react";

export default function AppNavbar() {
    return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
        <h1 className="text-lg font-semibold text-gray-800">AI Berichtsgenerator</h1>
        <div className="space-x-6">
          <a href="#" className="text-gray-600 hover:text-gray-900">
            Berichtseingabe
          </a>
        </div>
      </div>
    </nav>
  );
}