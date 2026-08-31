import { useState } from "react";
import { Play, ExternalLink } from "lucide-react";

const TOPIC_LABELS = {
  "global-macro": "Global Macro", "india-economy": "India", "energy": "Energy",
  "climate-finance": "Green Finance", "ai": "AI", "technology": "Tech",
  "fundraising": "Fundraising", "leadership": "Leadership", "geopolitics": "Geopolitics",
};

export const VideoCard = ({ video, onPlay }) => {
  const [playing, setPlaying] = useState(false);
  const topic = video.topics?.[0];

  const start = () => {
    setPlaying(true);
    if (onPlay) onPlay(topic, video.video_id);
  };

  return (
    <div
      data-testid={`video-card-${video.video_id}`}
      className="group flex flex-col overflow-hidden rounded-2xl border border-border bg-card transition-all duration-300 hover:-translate-y-1 hover:border-[hsl(var(--primary))]/50"
    >
      <div className="relative aspect-video w-full overflow-hidden bg-black">
        {playing ? (
          <iframe
            className="absolute inset-0 h-full w-full"
            src={`https://www.youtube.com/embed/${video.video_id}?autoplay=1&rel=0`}
            title={video.title}
            loading="lazy"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        ) : (
          <button
            onClick={start}
            data-testid={`video-play-${video.video_id}`}
            className="absolute inset-0 h-full w-full"
            aria-label={`Play ${video.title}`}
          >
            <img src={video.thumbnail} alt={video.title} loading="lazy"
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" />
            <span className="absolute inset-0 bg-black/25 transition-colors group-hover:bg-black/10" />
            <span className="absolute left-1/2 top-1/2 grid h-14 w-14 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] shadow-lg transition-transform group-hover:scale-110">
              <Play className="h-6 w-6 translate-x-0.5" fill="currentColor" />
            </span>
            {topic && (
              <span className="absolute left-3 top-3 rounded-full bg-black/70 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-[hsl(var(--primary))]">
                {TOPIC_LABELS[topic] || topic}
              </span>
            )}
          </button>
        )}
      </div>
      <div className="flex flex-1 flex-col p-4">
        <h3 className="line-clamp-2 text-sm font-semibold leading-snug text-foreground">{video.title}</h3>
        <a
          href={video.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-auto flex items-center gap-1.5 pt-3 text-xs font-medium text-muted-foreground transition-colors hover:text-[hsl(var(--primary))]"
          data-testid={`video-source-${video.video_id}`}
        >
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-[hsl(var(--primary))]" />
          Source: {video.source}
          <ExternalLink className="h-3 w-3" />
        </a>
      </div>
    </div>
  );
};

export default VideoCard;
