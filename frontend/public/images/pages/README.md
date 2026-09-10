# 레슨 페이지 이미지

대본 문장 1개 = 페이지 1장. 파일명 `pNN` 은 대본의 문장 번호와 같다.

    /images/pages/level{1,2,3}/lesson{01,02}/pNN.png     520 x 445

## 레벨 간 공유

Lesson 1·2는 세 레벨의 장면 비트가 같다(영어 난이도만 다름). 그래서 같은 그림을
공유하고, 대본이 실제로 갈리는 아래 세 페이지만 레벨 전용으로 따로 그렸다.

| 페이지 | 사유 |
|---|---|
| `level3/lesson01/p10` | 말하는 사람이 포포 → **피피**로 바뀐다 |
| `level2/lesson02/p11` | Level 1에 없는 11번째 문장 (포포가 뿌듯해한다) |
| `level3/lesson02/p11` | Level 1에 없는 11번째 문장 (기기가 포포에게 건네는 말) |

Level 1 Lesson 2만 10페이지, 나머지는 모두 11페이지다.

## 연결

`pages.json` 에 레슨별 URL 목록이 있다. 시딩할 때 콘텐츠 JSON의 빈 `image_path`
필드를 이 값으로 채우면 `import_ai_content.py` → `page.image_url` →
프론트 `<img src={imageUrl}>` 로 이어진다.
