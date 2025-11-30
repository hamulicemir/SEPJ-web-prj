export const mockQuestions = [
  {
    id: "q1",
    incident_type: "einbruch",
    question_key: "when",
    label: "Wann passierte es?",
    answer_type: "datetime",
    required: true,
    order_index: 10
  },
  {
    id: "q2",
    incident_type: "einbruch",
    question_key: "where",
    label: "Wo passierte es?",
    answer_type: "string",
    required: true,
    order_index: 20
  },
  {
    id: "q3",
    incident_type: "koerperverletzung",
    question_key: "opfer",
    label: "Wer ist das Opfer?",
    answer_type: "people[]",
    required: true,
    order_index: 40
  }
];
