import { Link } from "react-router-dom";

export default function AppNavbar() {
  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
        <h1 className="text-lg font-semibold text-gray-800">AI Berichtsgenerator</h1>

        <div className="space-x-6">
          <Link to="/" className="text-gray-600 hover:text-gray-900">
            Berichtseingabe
          </Link>

          <Link to="/admin" className="text-gray-600 hover:text-gray-900">
            Admin
          </Link>
        </div>
      </div>
    </nav>
  );
}
