import { Link } from "react-router-dom";
import { Navbar, NavbarBrand, NavbarCollapse, NavbarLink, NavbarToggle } from "flowbite-react";

function MyNavbar() {
  return (
    <Navbar fluid rounded>
      <NavbarBrand as={Link} to="/">
        <span className="self-center whitespace-nowrap text-xl font-semibold dark:text-white">
          AI Report Generator
        </span>
      </NavbarBrand>
      <NavbarToggle />
      <NavbarCollapse>
        <NavbarLink as={Link} to="/ReportGenerator" active>
          ReportGenerator
        </NavbarLink>
        <NavbarLink as={Link} to="/Dashboard">
          Dashboard
        </NavbarLink>
      </NavbarCollapse>
    </Navbar>
  );
}

export default MyNavbar;