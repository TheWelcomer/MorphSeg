<script>
  import Bubbles from "./Bubbles.svelte"

  const Stage = {
    BEFORE: 0,
    WORDS: 1,
    CLEANUP: 2,
    MORPHEMES: 3,
  };

  let input = $state("What the Segma?");
  let stage = $state(Stage.BEFORE);
  let words = $state(splitWords(input));
  let morphemes = $state([["What"],["the"],["Seg","ma"]]);
  
  function splitWords(text) {
    return text.replace(/\s/g, " ").split(" ");
  }

  function segment(text) {
    return text.split(" ").map((word)=>word.split(""));
  }

  export function startAnimation(){
    words = splitWords(input);
    stage++;
  }
</script>

<div id=cutting-board>
  {#if stage == Stage.BEFORE}
    <div id=cutting-board-input bind:innerText={input} contenteditable=true />
  {:else if stage >= Stage.WORDS}
    <div id="word-container">
      {#if stage != Stage.MORPHEMES}
        {#each words as word}
          <span class="word">
              <span class="word-inner">
                {word}
              </span>
          </span>&nbsp<span class="word-spacer" />
        {/each}
      {:else}
        {#each morphemes as word}
          {#each word as morpheme, mIndex}
            <span class="word">
                <span class="word-inner">
                  {morpheme}
                </span>{#if mIndex != (word.length - 1)}
                  <span class="morpheme-spacer" />
                {/if}
            </span>
          {/each}&nbsp<span class="canon-word-spacer" />
        {/each}
      {/if}
    </div>
  {/if}
  {#if stage >= Stage.CLEANUP}
    <Bubbles />
  {/if}
</div>

<style>
  @import "./style.css";
  
  #cutting-board {
    align-items: center;
    justify-content: center;
    display: flex;
  }

  #word-container {
    width: 100%;
    margin: 2em;  
  }

  .word {
    display: inline-block;
    margin: 0.25em 0 0.25em 0;
  }

  .word-inner {
    background-color: blue;
    padding: 0.1em;
  }

  .word-spacer {
    animation: 1s ease-out 0.2s 1 both expand;
    animation-iteration-count: 1;
    display: inline-block;
  }

  .morpheme-spacer {
    animation: 1s ease-out 0.2s 1 both expand-less;
    animation-iteration-count: 1;
    display: inline-block;
  }

  .canon-word-spacer {
    display: inline-block;
    width: 1em;
  }


  @keyframes expand {
    from {
      width: 0em;
    }
    to {
      width: 1.0em;
    }
  }

  @keyframes expand-less {
    from {
      width: 0em;
    }
    to {
      width: 0.5em;
    }
  }
</style>
