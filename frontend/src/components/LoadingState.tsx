interface LoadingStateProps {
  stageMessage: string;
}

export function LoadingState({ stageMessage }: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-8">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black mb-4"></div>
      <p className="text-[#999999]">{stageMessage}</p>
    </div>
  );
}
