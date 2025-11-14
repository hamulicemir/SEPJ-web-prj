import React, { useState } from "react";
import { Label, Textarea, Card } from "flowbite-react";
import Navbar from "./components/Navbar.jsx";

export default function App() {
  const [message, setMessage] = useState("");

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 flex flex-col" data-theme="light">

      <div className="flex flex-1 items-center justify-center px-6 py-12">
        <Card className="w-full max-w-4xl bg-white shadow-lg p-10 min-h-[50vh]">
          <h1 className="text-3xl font-semibold mb-6 text-gray-800">
            Berichterstellung
          </h1>

          <div className="flex flex-col gap-4">
            <Label htmlFor="message" value="Your message" className="text-lg" />

            <Textarea
              id="message"
              rows={12}
              placeholder="Write your thoughts here..."
              className="min-h-[40vh] bg-white !text-gray-900 border-gray-300 focus:ring-blue-500 focus:border-blue-500"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
          </div>
        </Card>
      </div>
    </div>
  );
}
