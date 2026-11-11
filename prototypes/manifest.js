// Список фич для главного меню и панели переключения.
// Новый прототип: добавьте объект сюда и пути к его страницам в views.
// Пути — от корня репозитория. Узел — node-id секции в Figma «Redesign (Student)».
window.SU10_FIGMA = "https://www.figma.com/design/KhMjdqizE1KUp3RsScJKne/Redesign--Student-?node-id=";

window.SU10_FEATURES = [
  {
    id: "onboarding",
    title: "Онбординг",
    about: "Тур после обновления кабинета: курсы, JuzAI, задачи, разделы.",
    node: "198-46719",
    views: [
      { id: "mobile", label: "Телефон", path: "prototypes/onboarding/index.html" },
      { id: "desktop", label: "Десктоп", path: "prototypes/onboarding/desktop.html" },
    ],
  },
  { id: "home", title: "Главная", about: "Истории, баннеры, быстрые ссылки.", node: "5-69692", views: [] },
  { id: "courses", title: "Курсы", about: "Список курсов, архив, сертификаты.", node: "5-7771", views: [] },
  { id: "course-page", title: "Страница курса", about: "Недели, прогресс, следующий урок.", node: "5-3210", views: [] },
  { id: "lessons", title: "Список уроков", about: "Уроки недели и их статусы.", node: "5-6544", views: [] },
  { id: "juzai", title: "JuzAI", about: "Чат с ассистентом по урокам и заданиям.", node: "492-24785", views: [] },
  { id: "articles", title: "Статьи", about: "Лента статей и страница статьи.", node: "433-35294", views: [] },
  { id: "status-survey", title: "Статус на следующий месяц", about: "Опрос о планах на следующий месяц.", node: "840-20566", views: [] },
  { id: "consult-feedback", title: "Отзыв о консультации", about: "Оценка консультации после встречи.", node: "840-48515", views: [] },
];
