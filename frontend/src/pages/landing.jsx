import React, { useState } from "react";
import { Label, Textarea, Card } from 'flowbite-react';

export default function App() {
  const [message, setMessage] = useState("");

  return (
    <div className="min-h-dvh bg-gray-50">
          <div className="max-w-md mx-auto pt-10 p-4">
            <Card className="border border-gray-200">
              <h1 className="text-xl font-semibold mb-2">Berichterstellung</h1>

              <div className="space-y-2">
                <div className="flex flex-col gap-2">
                  <Label htmlFor="message" value="Your message" />
                  <Textarea
                    id="message"
                    rows={4}
                    placeholder="Write your thoughts here..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                  />
                </div>
              </div>
            </Card>
          </div>
        </div>
    );
}