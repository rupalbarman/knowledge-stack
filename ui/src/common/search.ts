export type SearchHit = {
  file_id: string;
  file_name: string;
  chunk_index: number;
  text: string;
  score: number;
};

export type SearchResponse = {
  hits: SearchHit[];
};
