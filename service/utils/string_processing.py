from natasha import (
Doc ,
Segmenter ,
MorphVocab ,
NewsEmbedding ,
NewsMorphTagger ,
NewsSyntaxParser 
)

segmenter =Segmenter ()
emb =NewsEmbedding ()
morph_tagger =NewsMorphTagger (emb )
syntax_parser =NewsSyntaxParser (emb )
morph_vocab =MorphVocab ()

def string_processing (text ):
    """
    Метод для обработки текста
    :param text: Текст для обработки
    :return: Обработанный текст
    """
    doc =Doc (text )
    doc .segment (segmenter )
    doc .tag_morph (morph_tagger )
    doc .parse_syntax (syntax_parser )

    processed =set ()
    result =[]

    for token in doc .tokens :
        if token .id in processed :
            continue 

        if token .pos =="NOUN":
            adj_phrases =[]

            for adj_token in doc .tokens :
                if (
                adj_token .pos =="ADJ"
                and adj_token .head_id ==token .id 
                and adj_token .rel =="amod"
                ):
                    adj_token .lemmatize (morph_vocab )
                    adj_phrases .append (adj_token .lemma .lower ())
                    processed .add (adj_token .id )

            token .lemmatize (morph_vocab )
            phrase =" ".join (adj_phrases +[token .lemma .lower ()])
            result .append (phrase )
            processed .add (token .id )

    return result 