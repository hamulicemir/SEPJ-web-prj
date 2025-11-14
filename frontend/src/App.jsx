import React, { useState } from "react";
import { Label, Textarea, Card, Button } from "flowbite-react";
import Navbar from "./components/Navbar.jsx";

export default function App() {
  const [message, setMessage] = useState("");

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900" data-theme="light">
      <div className="flex flex-col items-center justify-center px-6 py-10 space-y-8 pt-4">
        {/* Eingabe Card*/}
        <Card className="w-full max-w-4xl bg-white shadow-lg p-10 min-h-[50vh]">
          <h1 className="text-3xl font-semibold mb-2 text-gray-800">
            Texteingabe des Berichts
          </h1>

          <div className="flex flex-col gap-3">
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
          <div className="flex justify-end mt-1">
            <Button
              color="blue"
              onClick={() => alert("Bericht gesendet!")}
              disabled={!message.trim()}
            >
              Bericht analysieren
            </Button>
          </div>
        </Card>
        {/* Ausgabe Card*/}
        <Card className="w-full max-w-4xl bg-white shadow-md p-2">
          <h2 className="text-2xl font-semibold mb-2 text-gray-800">
            Berichtsausgabe
          </h2>
          <div className="whitespace-pre-wrap text-gray-700">
            {message}
          </div>
        </Card>
      </div>
    </div>
  );
}
