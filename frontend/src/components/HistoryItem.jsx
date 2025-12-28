export default function HistoryItem({ item, onClick }) {
  return (
    <div 
      onClick={() => onClick(item)}
      className="border-b border-gray-200 bg-white hover:bg-blue-50 cursor-pointer transition-colors p-4 group"
    >
      <div className="flex justify-between items-start mb-1">
        <h3 className="font-semibold text-gray-800 text-sm truncate w-40" title={item.title}>
          {item.title}
        </h3>
        <span className="text-[10px] text-gray-400 whitespace-nowrap">
          {new Date(item.date).toLocaleDateString()}
        </span>
      </div>
      
      <p className="text-xs text-gray-500 line-clamp-2 mb-2">
        {item.preview}
      </p>
      
      <div className="flex justify-end">
        <span className="text-[10px] font-bold text-blue-600 group-hover:underline opacity-0 group-hover:opacity-100 transition-opacity">
          Details anzeigen &rarr;
        </span>
      </div>
    </div>
  );
}